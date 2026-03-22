import json
import tempfile
from subprocess import DEVNULL, Popen, TimeoutExpired

import boto3
import bson
import httpx
import redis
import structlog
from asgi_correlation_id.extensions.celery import load_correlation_ids
from botocore.exceptions import ClientError
from celery import Celery, signals
from celery.exceptions import MaxRetriesExceededError
from pydantic import ValidationError
from pymongo import MongoClient

from v2g.core.config import settings
from v2g.logger import configure_logging
from v2g.modules.conversions.models import ConversionStatus, ConversionWebhookBody

load_correlation_ids()

logger = structlog.get_logger()

celery_app = Celery(
    main='v2g_celery',
    broker=settings.get_celery_broker_dsn(),
)
celery_app.conf.broker_transport_options = settings.get_celery_broker_transport_options()

mongo_client = MongoClient(
    host=settings.mongodb.host,
    port=settings.mongodb.port,
    connect=False,
)

redis_client = redis.Redis(
    host=settings.redis.host,
    port=settings.redis.port,
)

s3_client = boto3.client('s3')


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


def _set_conversion_status(collection, conversion_id, owner_id, status, extra=None):
    fields = {'status': str(status)}
    if extra:
        fields.update(extra)

    collection.update_one({'_id': conversion_id}, {'$set': fields})

    message = {'conversion_id': str(conversion_id), 'status': str(status)}
    if extra and 'gif_file_id' in extra:
        message['gif_file_id'] = str(extra['gif_file_id'])

    redis_client.publish(f'user:{owner_id}:events', json.dumps(message))


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

    owner_id = conversion['owner_id']
    _set_conversion_status(collection, conversion_id, owner_id, ConversionStatus.PROCESSING)

    video_file_id = conversion['video_file_id']

    try:
        video_object = s3_client.get_object(Bucket=settings.s3.bucket, Key=str(video_file_id))
    except ClientError:
        log.error('Could not obtain a video file from the S3 bucket.', video_file_id=video_file_id)
        _set_conversion_status(collection, conversion_id, owner_id, ConversionStatus.FAILED)
        return

    with tempfile.NamedTemporaryFile('wb') as file_input:
        file_input.write(video_object['Body'].read())
        file_input.flush()

        # We have to specify the .gif suffix so ffmpeg understands the format of the output file.
        with tempfile.NamedTemporaryFile('rb', suffix='.gif') as file_output:
            # We use -y to automatically agree on file replacement.
            popen = Popen(
                ['ffmpeg', '-y', '-i', file_input.name, file_output.name],
                stdout=DEVNULL,
                stderr=DEVNULL,
            )

            timeout = settings.conversion_process_timeout_in_seconds
            try:
                code = popen.wait(timeout=timeout)
            except TimeoutExpired:
                log.error('Conversion timed out.', timeout=timeout)
                try:
                    raise self.retry()
                except MaxRetriesExceededError:
                    log.error('Max retries exceeded after timeout.')
                    _set_conversion_status(
                        collection,
                        conversion_id,
                        owner_id,
                        ConversionStatus.FAILED,
                    )
                    return

            if code != 0:
                log.error('ffmpeg failed', exit_code=code)
                try:
                    raise self.retry()
                except MaxRetriesExceededError:
                    log.error('Max retries exceeded after ffmpeg failure.')
                    _set_conversion_status(
                        collection,
                        conversion_id,
                        owner_id,
                        ConversionStatus.FAILED,
                    )
                    return

            gif_file_id = bson.ObjectId()
            gif_s3_key = str(gif_file_id)
            s3_client.put_object(
                Bucket=settings.s3.bucket,
                Key=gif_s3_key,
                Body=file_output,
                ContentType='image/gif',
                Metadata={'owner-id': str(owner_id)},
            )
            gif_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.s3.bucket, 'Key': gif_s3_key},
                ExpiresIn=settings.s3.presigned_url_expiry,
            )
            _set_conversion_status(
                collection,
                conversion_id,
                owner_id,
                ConversionStatus.DONE,
                extra={'gif_file_id': gif_file_id, 'gif_url': gif_url},
            )

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
