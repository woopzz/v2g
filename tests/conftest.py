import pytest
from pymongo import AsyncMongoClient

from v2g.config import settings


@pytest.fixture
def mongo_client():
    return AsyncMongoClient(
        host=settings.mongodb.host,
        port=settings.mongodb.port,
    )
