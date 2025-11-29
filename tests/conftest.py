from pathlib import Path

import pytest
from pymongo import AsyncMongoClient

from v2g.core.config import settings


@pytest.fixture
def mongo_client():
    return AsyncMongoClient(
        host=settings.mongodb.host,
        port=settings.mongodb.port,
    )


@pytest.fixture
def video_file():
    test_dir = Path(__file__).parent
    with open(test_dir / 'cat.mp4', 'rb') as file:
        yield file
