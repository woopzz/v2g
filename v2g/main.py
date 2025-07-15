import logging
import tempfile
import mimetypes
from subprocess import Popen

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

import gridfs
from pymongo import AsyncMongoClient
from bson import ObjectId

from v2g.config import settings

logging.basicConfig(level=logging.INFO)

app = FastAPI()
mongo_client = AsyncMongoClient(
    host=settings.mongodb.host,
    port=settings.mongodb.port,
)

@app.post('/')
async def convert_video(file: UploadFile):
    filename = file.filename
    content_type = calc_mimetype(file.content_type, filename)

    metadata = {}
    if content_type:
        metadata['contentType'] = content_type

    db = mongo_client.get_database(settings.mongodb.dbname)
    bucket = gridfs.AsyncGridFSBucket(db, 'files')
    mongo_video_id = await bucket.upload_from_stream(filename or '', file, metadata=metadata)

    file.file.seek(0)
    mongo_gif_id = await convert_video_to_gif(file)

    conversion = {'video_file_id': mongo_video_id, 'gif_file_id': mongo_gif_id}

    collection = db.get_collection('conversions')
    inserted_result = await collection.insert_one(conversion)
    conversion_id = inserted_result.inserted_id

    return {'id': str(conversion_id), 'video_file_id': str(mongo_video_id), 'gif_file_id': str(mongo_gif_id)}

@app.get('/conversion/{conversion_id}')
async def get_conversion(conversion_id: str):
    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('conversions')

    conversion = await collection.find_one({'_id': ObjectId(conversion_id)})
    if not conversion:
        raise HTTPException(status_code=404)

    return {
        'id': str(conversion['_id']),
        'video_file_id': str(conversion['video_file_id']),
        'gif_file_id': conversion['gif_file_id'] and str(conversion['gif_file_id']),
    }

@app.get('/file/{file_id}')
async def get_file(file_id: str):
    db = mongo_client.get_database(settings.mongodb.dbname)
    bucket = gridfs.AsyncGridFSBucket(db, 'files')

    try:
        stream = await bucket.open_download_stream(ObjectId(file_id))
    except gridfs.NoFile:
        raise HTTPException(status_code=404)

    metadata = stream.metadata
    media_type = metadata and metadata.get('contentType') or None

    return StreamingResponse(stream, media_type=media_type)

def calc_mimetype(file_mimetype, filename):
    if file_mimetype and file_mimetype.startswith('video/'):
        return file_mimetype

    if filename:
        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype:
            return mimetype

    return None

async def convert_video_to_gif(file: UploadFile):
    with tempfile.NamedTemporaryFile('wb') as file_input:
        file_input.write(await file.read())

        # We have to specify the .gif suffix so ffmpeg understands the format of the output file.
        with tempfile.NamedTemporaryFile('rb', suffix='.gif') as file_output:
            # We use -y to automatically agree on file replacement.
            popen = Popen(['ffmpeg', '-y', '-i', file_input.name, file_output.name])
            code = popen.wait()
            if code != 0:
                logging.error(f'Could convert a video file to a gif file. ffmpeg exit code: {code}')
                raise Exception(f'Could convert a video file to a gif file. ffmpeg exit code: {code}')

            db = mongo_client.get_database(settings.mongodb.dbname)
            bucket = gridfs.AsyncGridFSBucket(db, 'files')
            metadata = {'contentType': 'image/gif'}
            mongo_gif_id = await bucket.upload_from_stream((file.filename or 'video') + '.gif', file_output, metadata=metadata)
            return mongo_gif_id

if __name__ == '__main__':
    import uvicorn
    import multiprocessing

    dev = settings.uvicorn.dev

    if dev:
        workers = 1
    else:
        workers = multiprocessing.cpu_count() * 2 + 1

    uvicorn.run(
        app='main:app',
        host=settings.uvicorn.host,
        port=settings.uvicorn.port,
        workers=workers,
        reload=dev,
    )
