import mimetypes
from typing import Annotated

import gridfs
from fastapi import Depends, Request

from v2g.core.database import MongoClientDep
from v2g.core.repository import BaseRepository

from .models import Conversion


class ConversionRepository(BaseRepository):
    def get_conversions_collection(self):
        return self.get_database().get_collection('conversions')

    def get_files_bucket(self):
        database = self.get_database()
        return gridfs.AsyncGridFSBucket(database, 'files')

    async def get(self, id_=None, owner_id=None, many=False):
        conversions_coll = self.get_conversions_collection()

        params = {}
        if id_:
            params['_id'] = id_
        if owner_id:
            params['owner_id'] = owner_id

        if many:
            return (Conversion(**x) async for x in conversions_coll.find(params))
        else:
            conversion = await conversions_coll.find_one(params)
            return conversion and Conversion(**conversion)

    async def create(self, file, filename, content_type, owner_id, webhook_url=None):
        metadata = {
            'owner_id': owner_id,
            'content_type': content_type,
        }
        files_bucket = self.get_files_bucket()
        video_file_id = await files_bucket.upload_from_stream(filename, file, metadata=metadata)

        conversion = {
            'owner_id': owner_id,
            'video_file_id': video_file_id,
            'gif_file_id': None,
            'webhook_url': webhook_url,
        }

        conversions_coll = self.get_conversions_collection()
        result = await conversions_coll.insert_one(conversion)
        conversion_id = result.inserted_id
        return conversion_id, video_file_id

    def calc_mimetype(self, file_mimetype, filename):
        prefix = 'video/'

        if file_mimetype and file_mimetype.startswith(prefix):
            return file_mimetype

        if filename:
            mimetype, _ = mimetypes.guess_type(filename)
            if mimetype and mimetype.startswith(prefix):
                return mimetype

        return None


async def get_conversion_repository(request: Request, mongo_client: MongoClientDep):
    return ConversionRepository(request=request, mongo_client=mongo_client)


ConversionRepositoryDep = Annotated[ConversionRepository, Depends(get_conversion_repository)]
