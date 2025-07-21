import secrets

from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class UvicornConfig(BaseModel):
    dev: bool = False
    host: str = '0.0.0.0'
    port: int = 8000


class MongoDBConfig(BaseModel):
    host: str = 'mongo'
    port: int = 27017
    dbname: str = 'general'


class RedisConfig(BaseModel):
    host: str = 'redis'
    port: int = 6379


class Settings(BaseSettings):
    workdir: str
    secret: str = secrets.token_urlsafe(32)
    jwt_lifetime_in_minutes: int = 60 * 24 * 7
    conversion_process_timeout_in_seconds: int = 60 * 3

    model_config = SettingsConfigDict(env_nested_delimiter='__')
    uvicorn: UvicornConfig = Field(default_factory=UvicornConfig)
    mongodb: MongoDBConfig = Field(default_factory=MongoDBConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)


settings = Settings()
