import mimetypes
from typing import Annotated

import bson
from fastapi import Depends, Request

from v2g.core.config import settings
from v2g.core.database import MongoClientDep
from v2g.core.repository import BaseRepository
from v2g.core.s3 import S3ClientDep

from .models import ConversionPublic, ConversionStatus


class ConversionRepository(BaseRepository):
    def __init__(self, *, s3_client, **kwargs):
        super().__init__(**kwargs)
        self.s3_client = s3_client

    def get_conversions_collection(self):
        return self.get_database().get_collection('conversions')

    async def get(self, id_=None, owner_id=None, many=False):
        conversions_coll = self.get_conversions_collection()

        params = {}
        if id_:
            params['_id'] = id_
        if owner_id:
            params['owner_id'] = owner_id

        if many:
            return (
                self._convert_mongo_conversion_to_public(x)
                async for x in conversions_coll.find(params)
            )
        else:
            conversion = await conversions_coll.find_one(params)
            if conversion:
                return self._convert_mongo_conversion_to_public(conversion)
            else:
                return None

    async def create(self, file, content_type, owner_id, webhook_url=None):
        video_file_id = bson.ObjectId()
        s3key = str(video_file_id)
        await self.s3_client.put_object(
            Bucket=settings.s3.bucket,
            Key=s3key,
            Body=file,
            ContentType=content_type,
            Metadata={'owner-id': str(owner_id)},
        )

        conversion = {
            'owner_id': owner_id,
            'video_file_id': video_file_id,
            'gif_file_id': None,
            'gif_url': None,
            'webhook_url': webhook_url,
            'status': ConversionStatus.PENDING,
        }

        conversions_coll = self.get_conversions_collection()
        result = await conversions_coll.insert_one(conversion)
        conversion_id = result.inserted_id
        return conversion_id

    def calc_mimetype(self, file_mimetype, filename):
        prefix = 'video/'

        if file_mimetype and file_mimetype.startswith(prefix):
            return file_mimetype

        if filename:
            mimetype, _ = mimetypes.guess_type(filename)
            if mimetype and mimetype.startswith(prefix):
                return mimetype

        return None

    def _convert_mongo_conversion_to_public(self, data):
        return ConversionPublic.model_validate(
            {
                'id': str(data['_id']),
                **data,
            }
        )


async def get_conversion_repository(
    request: Request,
    mongo_client: MongoClientDep,
    s3_client: S3ClientDep,
):
    return ConversionRepository(request=request, mongo_client=mongo_client, s3_client=s3_client)


ConversionRepositoryDep = Annotated[ConversionRepository, Depends(get_conversion_repository)]
