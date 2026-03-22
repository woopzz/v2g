from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from pydantic import HttpUrl

from v2g.core.config import settings
from v2g.core.models import TypeObjectId
from v2g.core.utils import create_error_responses
from v2g.modules.users.dependencies import CurrentUserIDDep
from v2g.rate_limiter import limiter
from v2g.tasks import convert_video_to_gif

from .models import ConversionPublic, ConversionStatus
from .repositories import ConversionRepositoryDep

router = APIRouter()


@router.post(
    path='/',
    response_model=ConversionPublic,
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
    conversion_bson_id = await conversion_repo.create(
        file.file,
        content_type,
        current_user_id,
        webhook_url=webhook_url,
    )
    conversion_id = str(conversion_bson_id)
    convert_video_to_gif.delay(conversion_id)
    return {
        'id': conversion_id,
        'gif_url': None,
        'webhook_url': webhook_url,
        'status': ConversionStatus.PENDING,
    }


@router.get(
    path='/{conversion_id}/',
    response_model=ConversionPublic,
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
