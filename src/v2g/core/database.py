from typing import Annotated

from fastapi import Depends, Request
from pymongo import AsyncMongoClient


async def get_mongo_client(request: Request):
    return request.state.mongo_client


MongoClientDep = Annotated[AsyncMongoClient, Depends(get_mongo_client)]
