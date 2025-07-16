import bson
import pytest
from fastapi.testclient import TestClient

from v2g.main import app

@pytest.mark.asyncio
async def test_should_get_404_if_there_is_no_conversion():
    with TestClient(app) as client:
        conversation_id = bson.ObjectId()
        response = client.get(f'/conversion/{conversation_id}')
        assert response.status_code == 404
        assert response.json() == {'detail': 'Not Found'}

@pytest.mark.asyncio
async def test_should_get_404_if_there_is_no_file():
    with TestClient(app) as client:
        conversation_id = bson.ObjectId()
        response = client.get(f'/conversion/file/{conversation_id}')
        assert response.status_code == 404
        assert response.json() == {'detail': 'Not Found'}
