import mimetypes
from typing import BinaryIO

from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

import bson
import gridfs
from pymongo import AsyncMongoClient

from v2g.config import settings
from v2g.models import TypeObjectId, Conversion
from v2g.tasks import convert_video_to_gif
from .dependencies import MongoClientDep, CurrentUser
from .utils import create_error_responses

router = APIRouter()

@router.post(
    path='/',
    response_model=Conversion,
    summary='Run new conversion',
    responses=create_error_responses({400}, add_token_related_errors=True),
)
async def convert_video(file: UploadFile, mongo_client: MongoClientDep, current_user: CurrentUser):
    filename = file.filename

    content_type = calc_mimetype(file.content_type, filename)
    if not content_type:
        raise HTTPException(status_code=400, detail='Invalid media type. Expected video/*')

    conversion = await create_conversion(
        file.file, filename or '', content_type,
        current_user.id, mongo_client,
    )

    convert_video_to_gif.delay(str(conversion['_id']))

    return conversion

@router.get(
    path='/{conversion_id}/',
    response_model=Conversion,
    summary='Get conversion info',
    responses=create_error_responses({404}, add_token_related_errors=True),
)
async def get_conversion(conversion_id: TypeObjectId, mongo_client: MongoClientDep, current_user: CurrentUser):
    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('conversions')

    conversion = await collection.find_one({'_id': conversion_id, 'owner_id': current_user.id})
    if not conversion:
        raise HTTPException(status_code=404)

    return conversion

@router.get(
    path='/file/{file_id}/',
    summary='Get file content (video or gif)',
    responses={
        **create_error_responses({404}, add_token_related_errors=True),
        200: {'description': 'Returns a file stream.'}
    },
    response_class=StreamingResponse,
)
async def get_file(file_id: TypeObjectId, mongo_client: MongoClientDep, current_user: CurrentUser):
    db = mongo_client.get_database(settings.mongodb.dbname)
    bucket = gridfs.AsyncGridFSBucket(db, 'files')

    try:
        stream = await bucket.open_download_stream(file_id)
    except gridfs.NoFile:
        raise HTTPException(status_code=404)

    metadata = stream.metadata

    if metadata['owner_id'] != current_user.id:
        raise HTTPException(status_code=404)

    return StreamingResponse(stream, media_type=metadata['content_type'])

def calc_mimetype(file_mimetype, filename):
    prefix = 'video/'

    if file_mimetype and file_mimetype.startswith(prefix):
        return file_mimetype

    if filename:
        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype and mimetype.startswith(prefix):
            return mimetype

    return None

async def create_conversion(
    file: BinaryIO, filename: str, content_type: str,
    owner_id: bson.ObjectId, mongo_client: AsyncMongoClient,
):
    metadata = {
        'owner_id': owner_id,
        'content_type': content_type,
    }
    db = mongo_client.get_database(settings.mongodb.dbname)
    bucket = gridfs.AsyncGridFSBucket(db, 'files')
    mongo_video_id = await bucket.upload_from_stream(filename, file, metadata=metadata)

    conversion = {'owner_id': owner_id, 'video_file_id': mongo_video_id, 'gif_file_id': None}

    collection = db.get_collection('conversions')
    inserted_result = await collection.insert_one(conversion)
    conversion_id = inserted_result.inserted_id

    conversion['_id'] = conversion_id
    return conversion
