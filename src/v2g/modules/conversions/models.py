from pydantic import Field

from v2g.core.models import BaseSchema, TypeObjectId


class Conversion(BaseSchema):
    id: TypeObjectId = Field(
        alias='_id',
        serialization_alias='id',
    )
    owner_id: TypeObjectId = Field(exclude=True)
    video_file_id: TypeObjectId
    gif_file_id: TypeObjectId | None
    webhook_url: str | None

    class Config:
        arbitrary_types_allowed = True


class ConversionWebhookBody(BaseSchema):
    id: TypeObjectId
    video_file_id: TypeObjectId
    gif_file_id: TypeObjectId

    class Config:
        arbitrary_types_allowed = True
