import tempfile
from subprocess import Popen, TimeoutExpired

import bson
import gridfs
import httpx
import structlog
from celery import Celery, signals
from pydantic import ValidationError
from pymongo import MongoClient

from v2g.core.config import settings
from v2g.logger import configure_logging
from v2g.modules.conversions.models import ConversionWebhookBody

logger = structlog.get_logger()

celery_app = Celery(
    main='v2g_celery',
    broker=settings.get_celery_broker_dsn(),
)

mongo_client = MongoClient(
    host=settings.mongodb.host,
    port=settings.mongodb.port,
)


@signals.after_setup_logger.connect
def on_after_setup_logger(*args, **kwargs):
    configure_logging('v2g_celery')


@signals.task_prerun.connect
def on_task_prerun(sender, task_id, task, **_):
    request = task.request
    structlog.contextvars.bind_contextvars(
        task_id=task_id,
        task_name=task.name,
        retries=request.retries,
    )


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def convert_video_to_gif(self, conversion_id: str):
    log = logger.bind(conversion_id=conversion_id)
    conversion_id = bson.ObjectId(conversion_id)

    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('conversions')

    conversion = collection.find_one({'_id': conversion_id})
    if not conversion:
        log.error('Conversion was not found.')
        return

    video_file_id = conversion['video_file_id']

    bucket = gridfs.GridFSBucket(db, 'files')
    video_grid_out = next(bucket.find({'_id': video_file_id}, limit=1), None)
    if not video_grid_out:
        log.error('Video file was not found.', video_file_id=video_file_id)
        return

    video_metadata = video_grid_out.metadata

    with tempfile.NamedTemporaryFile('wb') as file_input:
        bucket.download_to_stream(video_file_id, file_input)

        # We have to specify the .gif suffix so ffmpeg understands the format of the output file.
        with tempfile.NamedTemporaryFile('rb', suffix='.gif') as file_output:
            # We use -y to automatically agree on file replacement.
            popen = Popen(['ffmpeg', '-y', '-i', file_input.name, file_output.name])

            timeout = settings.conversion_process_timeout_in_seconds
            try:
                code = popen.wait(timeout=timeout)
            except TimeoutExpired:
                log.error('Conversion timed out.', timeout=timeout)
                raise self.retry()

            if code != 0:
                log.error('ffmpeg failed', exit_code=code)
                raise self.retry()

            metadata = {'content_type': 'image/gif', 'owner_id': video_metadata['owner_id']}
            mongo_gif_id = bucket.upload_from_stream('result.gif', file_output, metadata=metadata)
            collection.update_one({'_id': conversion_id}, {'$set': {'gif_file_id': mongo_gif_id}})

    webhook_url = conversion.get('webhook_url')
    if webhook_url:
        log.info(
            'Scheduling a webhook request to notify about conversion completion.',
            webhook_url=webhook_url,
        )
        send_webhook_conversion_done.delay(str(conversion_id))


@celery_app.task(
    bind=True,
    autoretry_for=(httpx.RequestError, httpx.HTTPStatusError),
    retry_kwargs={'max_retries': 8},
    retry_backoff=True,
    retry_jitter=True,
)
def send_webhook_conversion_done(self, conversion_id: str):
    log = logger.bind(conversion_id=conversion_id)
    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('conversions')
    conversion = collection.find_one({'_id': bson.ObjectId(conversion_id)})
    if not conversion:
        log.error('Conversion was not found.')
        return

    webhook_url = conversion.get('webhook_url')
    if not webhook_url:
        log.error('webhook_url was not provided.')
        return

    video_file_id = conversion['video_file_id']
    gif_file_id = conversion['gif_file_id']
    try:
        cwb = ConversionWebhookBody(
            id=conversion['_id'],
            video_file_id=video_file_id,
            gif_file_id=gif_file_id,
        )
    except ValidationError:
        log.exception(
            'Could not build conversion body.',
            video_file_id=video_file_id,
            gif_file_id=gif_file_id,
        )
        return

    with httpx.Client(timeout=5.0) as client:
        try:
            response = client.post(webhook_url, json=cwb.model_dump())
        except httpx.RequestError as exc:
            log.error('Webhook request failed.')
            raise exc

        if response.status_code >= 500:
            log.error(
                'Bad response to webhook request.',
                status_code=response.status_code,
                reason=response.reason_phrase,
            )
            raise httpx.HTTPStatusError(
                f'Server error: {response.status_code} {response.reason_phrase}',
                request=response.request,
                response=response,
            )

    log.info('Webhook request sent successfully.')
