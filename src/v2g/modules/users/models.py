from pydantic import Field

from v2g.core.models import BaseSchema, TypeObjectId
from v2g.modules.conversions.models import Conversion


class User(BaseSchema):
    id: TypeObjectId = Field(
        alias='_id',
        serialization_alias='id',
    )

    class Config:
        arbitrary_types_allowed = True


class UserCreate(BaseSchema):
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)


class UserPublic(BaseSchema):
    id: TypeObjectId = Field(
        alias='_id',
        serialization_alias='id',
    )
    username: str
    conversions: list[Conversion]

    class Config:
        title = 'User'
        arbitrary_types_allowed = True
