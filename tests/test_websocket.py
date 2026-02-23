import json
import threading
import time

import bson
import pytest
from fastapi.testclient import TestClient

from v2g.app import app
from v2g.core.config import settings

from .utils import create_user_and_token

URL_WS = f'{settings.api_v1_str}/ws/'


def wait_for_subscription(redis_client, channel, timeout=5.0):
    """Block until the WS handler has subscribed to the channel, to avoid losing messages."""
    deadline = time.monotonic() + timeout
    while dict(redis_client.pubsub_numsub(channel)).get(channel.encode(), 0) == 0:
        if time.monotonic() >= deadline:
            raise TimeoutError(f'No subscriber on {channel!r} after {timeout}s')
        time.sleep(0.01)


@pytest.mark.asyncio
async def test_ws_rejects_missing_token():
    with TestClient(app) as client:
        with pytest.raises(Exception):
            with client.websocket_connect(URL_WS):
                pass


@pytest.mark.asyncio
async def test_ws_rejects_invalid_token():
    with TestClient(app) as client:
        with pytest.raises(Exception):
            with client.websocket_connect(URL_WS + '?token=badtoken'):
                pass


@pytest.mark.asyncio
async def test_ws_forwards_redis_messages(mongo_client, redis_client):
    user_id, token = await create_user_and_token(mongo_client)
    channel = f'user:{user_id}:events'
    event = {
        'conversion_id': str(bson.ObjectId()),
        'status': 'done',
        'gif_file_id': str(bson.ObjectId()),
    }

    with TestClient(app) as client:
        with client.websocket_connect(URL_WS + f'?token={token.access_token}') as ws:

            def publish():
                wait_for_subscription(redis_client, channel)
                redis_client.publish(channel, json.dumps(event))

            t = threading.Thread(target=publish)
            t.start()
            received = json.loads(ws.receive_text())
            t.join()

    assert received == event


@pytest.mark.asyncio
async def test_ws_does_not_receive_other_users_events(mongo_client, redis_client):
    user_id, token = await create_user_and_token(mongo_client)
    other_user_id = bson.ObjectId()
    channel = f'user:{user_id}:events'

    own_event = {'conversion_id': str(bson.ObjectId()), 'status': 'done'}
    other_event = {'conversion_id': str(bson.ObjectId()), 'status': 'done'}

    def publish():
        wait_for_subscription(redis_client, channel)
        redis_client.publish(f'user:{other_user_id}:events', json.dumps(other_event))
        redis_client.publish(channel, json.dumps(own_event))

    with TestClient(app) as client:
        with client.websocket_connect(URL_WS + f'?token={token.access_token}') as ws:
            t = threading.Thread(target=publish)
            t.start()
            received = json.loads(ws.receive_text())
            t.join()

    assert received == own_event
