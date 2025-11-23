import io
import os.path
from unittest.mock import patch

import bson
import pytest
from fastapi.testclient import TestClient

from v2g.config import settings
from v2g.main import app
from v2g.routers.conversion import create_conversion
from v2g.tasks import convert_video_to_gif

from .utils import create_user_and_token


@pytest.mark.asyncio
@patch('v2g.routers.conversion.convert_video_to_gif')
async def test_conversion(mock_convert_video_to_gif, mongo_client):
    _, token = await create_user_and_token(mongo_client)

    with TestClient(app) as client:
        # Should run conversion.

        path_to_video = os.path.join(settings.workdir, 'tests', 'cat.mp4')
        with open(path_to_video, 'rb') as file_input:
            response = client.post(
                '/conversion',
                files={'file': file_input},
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

        # Trigger the conversion manually without messaging.

        convert_video_to_gif(conversion_id)

        # Should get the video file content.

        response = client.get(
            f'/conversion/file/{video_file_id}',
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 200
        assert response.headers['content-type'] == 'video/mp4'

        # Get the updated conversion info (with the gif file id).

        response = client.get(
            f'/conversion/{conversion_id}',
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 200

        result = response.json()
        assert result['id'] == conversion_id
        assert result['video_file_id'] == video_file_id

        gif_file_id = result['gif_file_id']
        assert gif_file_id and bson.ObjectId(gif_file_id)

        # Should get the gif file content.

        response = client.get(
            f'/conversion/file/{gif_file_id}',
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
            '/conversion',
            files={'file': file_input},
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 400
        assert response.json() == {'detail': 'Invalid media type. Expected video/*'}


@pytest.mark.asyncio
async def test_should_get_404_if_there_is_no_conversion(mongo_client):
    _, token = await create_user_and_token(mongo_client)

    with TestClient(app) as client:
        conversation_id = bson.ObjectId()
        response = client.get(
            f'/conversion/{conversation_id}',
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 404
        assert response.json() == {'detail': 'Not Found'}


@pytest.mark.asyncio
async def test_should_get_404_if_there_is_no_file(mongo_client):
    _, token = await create_user_and_token(mongo_client)

    with TestClient(app) as client:
        conversation_id = bson.ObjectId()
        response = client.get(
            f'/conversion/file/{conversation_id}',
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 404
        assert response.json() == {'detail': 'Not Found'}


@pytest.mark.asyncio
async def test_should_get_404_if_not_own_conversion(mongo_client):
    _, token = await create_user_and_token(mongo_client)

    another_user_id = bson.ObjectId()
    conversion = await create_conversion(
        io.BytesIO(b'123'),
        '',
        'example/example',
        another_user_id,
        mongo_client,
    )
    conversion_id = conversion['_id']

    with TestClient(app) as client:
        response = client.get(
            f'/conversion/{conversion_id}',
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 404
        assert response.json() == {'detail': 'Not Found'}


@pytest.mark.asyncio
async def test_should_get_404_if_not_own_file(mongo_client):
    _, token = await create_user_and_token(mongo_client)

    another_user_id = bson.ObjectId()
    conversion = await create_conversion(
        io.BytesIO(b'123'),
        '',
        'example/example',
        another_user_id,
        mongo_client,
    )
    video_file_id = conversion['video_file_id']

    with TestClient(app) as client:
        response = client.get(
            f'/conversion/file/{video_file_id}',
            headers={'Authorization': 'Bearer ' + token.access_token},
        )
        assert response.status_code == 404
        assert response.json() == {'detail': 'Not Found'}
