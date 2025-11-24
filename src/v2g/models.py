from typing import Any

import bson
from pydantic import BaseModel, Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, PydanticCustomError, core_schema


class TypeObjectId:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        def validate(value: str | bson.ObjectId) -> bson.ObjectId:
            try:
                return bson.ObjectId(value)
            except bson.errors.InvalidId:
                raise PydanticCustomError('invalid_bson_id', 'Cannot be a valid BSON id.')

        def serialize(value: bson.ObjectId) -> str:
            return str(value)

        validation_schema = core_schema.no_info_plain_validator_function(validate)
        serialization_schema = core_schema.plain_serializer_function_ser_schema(serialize)

        return core_schema.json_or_python_schema(
            json_schema=validation_schema,
            python_schema=validation_schema,
            serialization=serialization_schema,
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {
            'type': 'string',
            'format': 'objectid',
            'example': str(bson.ObjectId()),
        }


class ErrorResponse(BaseModel):
    detail: str

    class Config:
        title = 'Error'


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class User(BaseModel):
    id: TypeObjectId = Field(
        alias='_id',
        serialization_alias='id',
    )

    class Config:
        arbitrary_types_allowed = True


class UserCreate(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)


class UserPublic(BaseModel):
    id: TypeObjectId = Field(
        alias='_id',
        serialization_alias='id',
    )
    username: str
    conversions: list['Conversion']

    class Config:
        title = 'User'
        arbitrary_types_allowed = True


class Conversion(BaseModel):
    id: TypeObjectId = Field(
        alias='_id',
        serialization_alias='id',
    )
    owner_id: TypeObjectId = Field(exclude=True)
    video_file_id: TypeObjectId
    gif_file_id: TypeObjectId | None

    class Config:
        arbitrary_types_allowed = True
