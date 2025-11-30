import pytest
from fastapi.testclient import TestClient

from v2g.app import app
from v2g.core.config import settings

from .utils import create_user, delete_user

URL_AUTH = f'{settings.api_v1_str}/auth/'


@pytest.mark.asyncio
async def test_should_create_token(mongo_client):
    username = 'test'
    password = 'testtest'
    await create_user(username, password, mongo_client)

    with TestClient(app) as client:
        response = client.post(
            URL_AUTH + 'access-token',
            data={'username': username, 'password': password},
        )
        assert response.status_code == 200

        result = response.json()
        assert result['access_token']
        assert result['token_type'] == 'bearer'


@pytest.mark.asyncio
async def test_should_get_404_if_user_does_not_exist(mongo_client):
    username = 'test'
    password = 'testtest'
    await delete_user(username, mongo_client)

    with TestClient(app) as client:
        response = client.post(
            URL_AUTH + 'access-token',
            data={'username': username, 'password': password},
        )
        assert response.status_code == 404

        result = response.json()
        assert result['detail'] == 'Not found any user with these credentials.'
