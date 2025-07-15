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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter='__')
    uvicorn: UvicornConfig = Field(default_factory=UvicornConfig)
    mongodb: MongoDBConfig = Field(default_factory=MongoDBConfig)


settings = Settings()
