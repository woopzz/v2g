from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import AsyncMongoClient

from v2g.config import settings
from v2g.routers.conversion import router as router_conversion

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncMongoClient(
        host=settings.mongodb.host,
        port=settings.mongodb.port,
    ) as mongo_client:
        yield {'mongo_client': mongo_client}

app = FastAPI(lifespan=lifespan)
app.include_router(router_conversion, prefix='/conversion')

if __name__ == '__main__':
    import uvicorn
    import multiprocessing

    dev = settings.uvicorn.dev

    if dev:
        workers = 1
    else:
        workers = multiprocessing.cpu_count() * 2 + 1

    uvicorn.run(
        app='main:app',
        host=settings.uvicorn.host,
        port=settings.uvicorn.port,
        workers=workers,
        reload=dev,
    )
