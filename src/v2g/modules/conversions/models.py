from enum import StrEnum

from v2g.core.models import BaseSchema, TypeObjectId


class ConversionStatus(StrEnum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    DONE = 'done'
    FAILED = 'failed'


TERMINAL_CONVERSION_STATUSES = {
    ConversionStatus.DONE,
    ConversionStatus.FAILED,
}


class ConversionPublic(BaseSchema):
    id: str
    gif_url: str | None = None
    webhook_url: str | None
    status: ConversionStatus = ConversionStatus.PENDING

    class Config:
        title = 'Conversion'


class ConversionWebhookBody(BaseSchema):
    id: TypeObjectId
    video_file_id: TypeObjectId
    gif_file_id: TypeObjectId

    class Config:
        arbitrary_types_allowed = True
