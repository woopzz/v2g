import io
from unittest.mock import patch

import bson
import httpx
import pytest
from fastapi.testclient import TestClient

import v2g.tasks as tasks
from v2g.app import app
from v2g.core.config import settings
from v2g.modules.conversions.repositories import ConversionRepository

from .utils import create_user_and_token

URL_CONVERSIONS = f'{settings.api_v1_str}/conversions/'


def get_conversion_url(conversion_id):
    return URL_CONVERSIONS + str(conversion_id)


def get_file_url(file_id):
    return f'{URL_CONVERSIONS}file/{file_id}'


@pytest.mark.asyncio
async def test_conversion(mongo_client, video_file):
    webhook_url = 'http://localhost:8000/'
    _, token = await create_user_and_token(mongo_client)

    with TestClient(app) as client:
        # Should run conversion.

        convert_video_to_gif_ = 'v2g.modules.conversions.routes.convert_video_to_gif'
        with patch(convert_video_to_gif_) as mock_convert_video_to_gif:
            response = client.post(
                URL_CONVERSIONS,
                data={'webhook_url': webhook_url},
                files={'file': video_file},
                headers={'Authorization': 'Bearer ' + token.access_token},
            )
            assert response.status_code == 200
            result = response.json()

            conversion_id = result['id']
            video_file_id = result['video_file_id']
            gif_file_id = result['gif_file_id']

            assert conversion_id and bson.ObjectId(conversion_id)
            assert video_file_id and bson.ObjectId(video_file_id)
            assert gif_file_id is None

        mock_convert_video_to_gif.delay.assert_called_once_with(conversion_id)

        with patch('v2g.tasks.send_webhook_conversion_done') as mock_send_webhook_conversion_done:
            tasks.convert_video_to_gif(conversion_id)

        mock_send_webhook_conversion_done.delay.assert_called_once_with(conversion_id)

        with patch('httpx.Client.post') as mock_post:
            mock_post.return_value = httpx.Response(200)
            tasks.send_webhook_conversion_done(conversion_id)

        collection = mongo_client[settings.mongodb.dbname]['conversions']
        conversion = await collection.find_one({'_id': bson.ObjectId(conversion_id)})

        gif_file_id = conversion['gif_file_id']
        assert gif_file_id
        gif_file_id = str(gif_file_id)

        mock_post.assert_called_once_with(
            webhook_url,
            json={
                'id': conversion_id,
                'video_file_id': video_file_id,
                'gif_file_id': gif_file_id,
            },
        )

        # Should get the video file content.

        response = client.get(
            get_file_url(video_file_id),
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 200
        assert response.headers['content-type'] == 'video/mp4'

        # Get the updated conversion info (with the gif file id).

        response = client.get(
            get_conversion_url(conversion_id),
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 200

        result = response.json()
        assert result['id'] == conversion_id
        assert result['video_file_id'] == video_file_id
        assert result['gif_file_id'] == gif_file_id
        assert result['webhook_url'] == webhook_url

        # Should get the gif file content.

        response = client.get(
            get_file_url(gif_file_id),
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 200
        assert response.headers['content-type'] == 'image/gif'


@pytest.mark.asyncio
async def test_should_discard_conversion_if_invalid_media_type(mongo_client):
    _, token = await create_user_and_token(mongo_client)

    with TestClient(app) as client:
        file_input = io.BytesIO(b'qwerty')
        response = client.post(
            URL_CONVERSIONS,
            files={'file': file_input},
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 400
        assert response.json() == {'detail': 'Invalid media type. Expected video/*'}


@pytest.mark.asyncio
async def test_should_get_404_if_there_is_no_conversion(mongo_client):
    _, token = await create_user_and_token(mongo_client)

    with TestClient(app) as client:
        conversion_id = bson.ObjectId()
        response = client.get(
            get_conversion_url(conversion_id),
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 404
        assert response.json() == {'detail': 'Not Found'}


@pytest.mark.asyncio
async def test_should_get_404_if_there_is_no_file(mongo_client):
    _, token = await create_user_and_token(mongo_client)

    with TestClient(app) as client:
        file_id = bson.ObjectId()
        response = client.get(
            get_file_url(file_id),
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 404
        assert response.json() == {'detail': 'Not Found'}


@pytest.mark.asyncio
async def test_should_get_404_if_not_own_conversion(mongo_client):
    _, token = await create_user_and_token(mongo_client)

    another_user_id = bson.ObjectId()
    conversion_repo = ConversionRepository(request=None, mongo_client=mongo_client)
    conversion_id, _ = await conversion_repo.create(
        io.BytesIO(b'123'),
        '',
        'example/example',
        another_user_id,
    )

    with TestClient(app) as client:
        response = client.get(
            get_conversion_url(conversion_id),
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 404
        assert response.json() == {'detail': 'Not Found'}


@pytest.mark.asyncio
async def test_should_get_404_if_not_own_file(mongo_client):
    _, token = await create_user_and_token(mongo_client)

    another_user_id = bson.ObjectId()
    conversion_repo = ConversionRepository(request=None, mongo_client=mongo_client)
    _, video_file_id = await conversion_repo.create(
        io.BytesIO(b'123'),
        '',
        'example/example',
        another_user_id,
    )

    with TestClient(app) as client:
        response = client.get(
            get_file_url(video_file_id),
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 404
        assert response.json() == {'detail': 'Not Found'}
