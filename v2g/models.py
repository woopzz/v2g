from typing import Any

from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import CoreSchema, PydanticCustomError, core_schema

import bson


class TypeObjectId:

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        def validate(value: str) -> bson.ObjectId:
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


class Conversion(BaseModel):
    id: TypeObjectId = Field(
        alias='_id',
        serialization_alias='id',
    )
    video_file_id: TypeObjectId
    gif_file_id: TypeObjectId | None

    class Config:
        arbitrary_types_allowed = True
