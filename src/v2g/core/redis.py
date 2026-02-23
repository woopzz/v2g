from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, WebSocket


async def get_redis_client(websocket: WebSocket):
    return websocket.state.redis_client


RedisClientDep = Annotated[aioredis.Redis, Depends(get_redis_client)]
