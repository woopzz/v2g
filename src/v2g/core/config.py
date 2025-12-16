import secrets

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_PROMETHEUS_MULTIPROC_DIR = '/tmp/prometheus_multiproc_dir'
PATHES_TO_SKIP_METRICS_FOR = (
    '/favicon.ico',
    '/metrics',
    '/docs',
    '/openapi.json',
)


class UvicornConfig(BaseModel):
    host: str = '0.0.0.0'
    port: int = 8000
    workers: int = 1
    reload: bool = False


class MongoDBConfig(BaseModel):
    host: str = 'mongo'
    port: int = 27017
    dbname: str = 'general'


class RedisConfig(BaseModel):
    host: str = 'redis'
    port: int = 6379


class Settings(BaseSettings):
    api_v1_str: str = '/api/v1'
    secret: str = secrets.token_urlsafe(32)
    jwt_lifetime_in_minutes: int = 60 * 24 * 7
    conversion_process_timeout_in_seconds: int = 60 * 3

    rate_limit_enabled: bool = True
    rate_limit_create_conversions: str = '50/day; 10/hour'

    log_level: str = 'INFO'
    log_json: bool = False

    model_config = SettingsConfigDict(
        env_prefix='v2g_',
        env_nested_delimiter='_',
    )
    uvicorn: UvicornConfig = Field(default_factory=UvicornConfig)
    mongodb: MongoDBConfig = Field(default_factory=MongoDBConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    def get_rate_limit_dsn(self):
        return f'redis://{self.redis.host}:{self.redis.port}/1'

    def get_celery_broker_dsn(self):
        return f'redis://{self.redis.host}:{settings.redis.port}/2'


settings = Settings()
