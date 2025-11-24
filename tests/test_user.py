import bson
import pytest
from fastapi.testclient import TestClient

from v2g.main import app

from .utils import create_user, create_user_and_token, delete_user


@pytest.mark.asyncio
async def test_should_create_user(mongo_client):
    username = 'test'
    password = 'testtest'
    await delete_user(username, mongo_client)

    with TestClient(app) as client:
        response = client.post('/user', json={'username': username, 'password': password})
        assert response.status_code == 200

        result = response.json()
        assert len(result.keys())
        assert result['id'] and bson.ObjectId(result['id'])
        assert result['username'] == username
        assert result['conversions'] == []


@pytest.mark.asyncio
async def test_should_get_422_if_username_is_too_short():
    username = '1'
    password = 'testtest'

    with TestClient(app) as client:
        response = client.post('/user', json={'username': username, 'password': password})
        assert response.status_code == 422

        result = response.json()
        data = result['detail'][0]
        assert data['loc'] == ['body', 'username']
        assert data['msg'] == 'String should have at least 3 characters'


@pytest.mark.asyncio
async def test_should_get_422_if_password_is_too_short():
    username = 'test'
    password = 'test'

    with TestClient(app) as client:
        response = client.post('/user', json={'username': username, 'password': password})
        assert response.status_code == 422

        result = response.json()
        data = result['detail'][0]
        assert data['loc'] == ['body', 'password']
        assert data['msg'] == 'String should have at least 8 characters'


@pytest.mark.asyncio
async def test_should_get_400_if_user_exists(mongo_client):
    username = 'test'
    password = 'testtest'
    await create_user(username, password, mongo_client)

    with TestClient(app) as client:
        response = client.post('/user', json={'username': username, 'password': password})
        assert response.status_code == 400

        result = response.json()
        assert result['detail'] == 'This username is already taken.'


@pytest.mark.asyncio
async def test_should_get_my_user_info(mongo_client):
    username = 'test'
    password = 'testtest'
    user_id, token = await create_user_and_token(mongo_client, username=username, password=password)

    with TestClient(app) as client:
        response = client.get('/user/me', headers={'Authorization': 'Bearer ' + token.access_token})
        assert response.status_code == 200

        result = response.json()
        assert len(result.keys())
        assert result['id'] == str(user_id)
        assert result['username'] == username
        assert result['conversions'] == []


@pytest.mark.asyncio
async def test_should_get_401_if_no_token():
    with TestClient(app) as client:
        response = client.get('/user/me')
        assert response.status_code == 401

        result = response.json()
        assert result['detail'] == 'Not authenticated'
