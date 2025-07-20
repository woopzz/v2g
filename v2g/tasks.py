import tempfile
from subprocess import Popen

import bson
import gridfs
from pymongo import MongoClient

from celery import Celery
from celery.utils.log import get_task_logger

from v2g.config import settings

logger = get_task_logger(__name__)

celery_app = Celery(
    main='tasks',
    broker=f'redis://{settings.redis.host}:{settings.redis.port}/0',
)

mongo_client = MongoClient(
    host=settings.mongodb.host,
    port=settings.mongodb.port,
)

@celery_app.task(queue='conversion', bind=True, max_retries=3, default_retry_delay=30)
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
            code = popen.wait()
            if code != 0:
                logger.error(f'Could not convert a video file to a gif file. ffmpeg exit code: {code}. Conversion: {conversion}')
                raise self.retry()

            metadata = {'content_type': 'image/gif', 'owner_id': video_metadata['owner_id']}
            mongo_gif_id = bucket.upload_from_stream('result.gif', file_output, metadata=metadata)
            collection.update_one({'_id': conversion_id}, {'$set': {'gif_file_id': mongo_gif_id}})
