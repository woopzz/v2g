import tempfile
from subprocess import Popen, TimeoutExpired

import bson
import gridfs
import httpx
from celery import Celery
from celery.utils.log import get_task_logger
from pydantic import ValidationError
from pymongo import MongoClient

from v2g.config import settings
from v2g.models import ConversionWebhookBody

logger = get_task_logger(__name__)

celery_app = Celery(
    main='tasks',
    broker=settings.get_celery_broker_dsn(),
)

mongo_client = MongoClient(
    host=settings.mongodb.host,
    port=settings.mongodb.port,
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def convert_video_to_gif(self, conversion_id: str):
    conversion_id = bson.ObjectId(conversion_id)

    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('conversions')
    conversion = collection.find_one({'_id': conversion_id})
    video_file_id = conversion['video_file_id']

    bucket = gridfs.GridFSBucket(db, 'files')
    video_grid_out = next(bucket.find({'_id': video_file_id}, limit=1))
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
                logger.error(
                    f'Exceeded the time limit of {timeout} seconds. Conversion: {conversion}'
                )
                raise self.retry()

            if code != 0:
                logger.error(
                    f'Could not convert a video file to a gif file. ffmpeg exit code: {code}. Conversion: {conversion}'
                )
                raise self.retry()

            metadata = {'content_type': 'image/gif', 'owner_id': video_metadata['owner_id']}
            mongo_gif_id = bucket.upload_from_stream('result.gif', file_output, metadata=metadata)
            collection.update_one({'_id': conversion_id}, {'$set': {'gif_file_id': mongo_gif_id}})

    if conversion.get('webhook_url'):
        logger.info(
            'Scheduling a webhook request to notify about conversion completion. '
            f'Conversion ID: {conversion_id}'
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
    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('conversions')
    conversion = collection.find_one({'_id': bson.ObjectId(conversion_id)})
    if not conversion:
        logger.error(
            'Could not send a webhook request: conversion was not found. '
            f'Conversion ID: {conversion_id}'
        )
        return

    webhook_url = conversion.get('webhook_url')
    if not webhook_url:
        logger.warning(
            'Could not send a webhook request: webhook URL was not provided. '
            f'Conversion ID: {conversion_id}'
        )
        return

    try:
        cwb = ConversionWebhookBody(
            id=conversion['_id'],
            video_file_id=conversion['video_file_id'],
            gif_file_id=conversion['gif_file_id'],
        )
    except ValidationError as exc:
        logger.error(
            'Could not send a webhook request: invalid conversion record. '
            f'Conversion ID: {conversion_id}',
            exc_info=exc,
        )
        return

    with httpx.Client(timeout=5.0) as client:
        try:
            response = client.post(webhook_url, json=cwb.model_dump())
        except httpx.RequestError as exc:
            logger.error(
                f'Webhook request failed. Retry: {self.request.retries}. Conversion ID: {conversion_id}'
            )
            raise exc

        if response.status_code >= 500:
            logger.error(
                'Could not send a webhook request: bad response. '
                f'Response: {response.status_code} {response.reason_phrase} '
                f'Retry: {self.request.retries}. Conversion ID: {conversion_id}'
            )
            raise httpx.HTTPStatusError(
                f'Server error: {response.status_code} {response.reason_phrase}',
                request=response.request,
                response=response,
            )

    logger.info(f'Webhook request sent successfully. Conversion ID: {conversion_id}')
