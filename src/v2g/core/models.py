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


class BaseSchema(BaseModel):
    pass


class ErrorResponse(BaseSchema):
    detail: str

    class Config:
        title = 'Error'


class Token(BaseSchema):
    access_token: str
    token_type: str = 'bearer'


class User(BaseSchema):
    id: TypeObjectId = Field(
        alias='_id',
        serialization_alias='id',
    )

    class Config:
        arbitrary_types_allowed = True
