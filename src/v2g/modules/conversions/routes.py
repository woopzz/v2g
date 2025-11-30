from typing import Annotated

import gridfs
from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import HttpUrl

from v2g.core.config import settings
from v2g.core.models import TypeObjectId
from v2g.core.utils import create_error_responses
from v2g.modules.users.dependencies import CurrentUserIDDep
from v2g.rate_limiter import limiter
from v2g.tasks import convert_video_to_gif

from .models import Conversion
from .repositories import ConversionRepositoryDep

router = APIRouter()


@router.post(
    path='/',
    response_model=Conversion,
    summary='Run new conversion',
    responses=create_error_responses({400}, add_token_related_errors=True),
)
@limiter.limit(settings.rate_limit_create_conversions)
async def convert_video(
    *,
    file: UploadFile,
    webhook_url: Annotated[HttpUrl | None, Form()] = None,
    request: Request,
    current_user_id: CurrentUserIDDep,
    conversion_repo: ConversionRepositoryDep,
):
    filename = file.filename

    content_type = conversion_repo.calc_mimetype(file.content_type, filename)
    if not content_type:
        raise HTTPException(status_code=400, detail='Invalid media type. Expected video/*')

    webhook_url = webhook_url and webhook_url.unicode_string()
    conversion_id, video_file_id = await conversion_repo.create(
        file.file,
        filename or '',
        content_type,
        current_user_id,
        webhook_url=webhook_url,
    )
    convert_video_to_gif.delay(str(conversion_id))
    return {
        '_id': conversion_id,
        'owner_id': str(current_user_id),
        'video_file_id': video_file_id,
        'gif_file_id': None,
        'webhook_url': webhook_url,
    }


@router.get(
    path='/{conversion_id}/',
    response_model=Conversion,
    summary='Get conversion info',
    responses=create_error_responses({404}, add_token_related_errors=True),
)
async def get_conversion(
    conversion_id: TypeObjectId,
    current_user_id: CurrentUserIDDep,
    conversion_repo: ConversionRepositoryDep,
):
    conversion = await conversion_repo.get(id_=conversion_id, owner_id=current_user_id)
    if not conversion:
        raise HTTPException(status_code=404)

    return conversion


@router.get(
    path='/file/{file_id}/',
    summary='Get file content (video or gif)',
    responses={
        **create_error_responses({404}, add_token_related_errors=True),
        200: {'description': 'Returns a file stream.'},
    },
    response_class=StreamingResponse,
)
async def get_file(
    file_id: TypeObjectId,
    current_user_id: CurrentUserIDDep,
    conversion_repo: ConversionRepositoryDep,
):
    files_bucket = conversion_repo.get_files_bucket()

    try:
        stream = await files_bucket.open_download_stream(file_id)
    except gridfs.NoFile:
        raise HTTPException(status_code=404)

    metadata = stream.metadata

    if metadata['owner_id'] != current_user_id:
        raise HTTPException(status_code=404)

    return StreamingResponse(stream, media_type=metadata['content_type'])
