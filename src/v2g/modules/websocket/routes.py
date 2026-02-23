import asyncio

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import RedisError

from v2g.core.redis import RedisClientDep
from v2g.modules.users.dependencies import WsCurrentUserIDDep

logger = structlog.get_logger()
router = APIRouter()


@router.websocket('/ws/')
async def client_ws(
    websocket: WebSocket,
    current_user_id: WsCurrentUserIDDep,
    redis_client: RedisClientDep,
):
    await websocket.accept()

    log = logger.bind(user_id=str(current_user_id))
    pubsub = redis_client.pubsub()
    channel = f'user:{current_user_id}:events'

    async def reader():
        try:
            while True:
                await websocket.receive()
        except WebSocketDisconnect:
            log.info('Client disconnected.')

    reader_task = asyncio.create_task(reader())
    try:
        await pubsub.subscribe(channel)
        while not reader_task.done():
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None:
                continue
            await websocket.send_text(message['data'].decode())
    except WebSocketDisconnect:
        log.info('Client disconnected during send.')
    except RedisError:
        log.exception('Redis error in WebSocket handler.')
    finally:
        reader_task.cancel()
        try:
            await websocket.close()
        except Exception:
            log.info('Failed to close WebSocket.')
        try:
            await pubsub.aclose()
        except Exception:
            log.warning('Failed to close pubsub.')
