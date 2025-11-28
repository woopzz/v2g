from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pymongo import AsyncMongoClient

from v2g.models import User
from v2g.security import parse_token


async def get_mongo_client(request: Request):
    return request.state.mongo_client


MongoClientDep = Annotated[AsyncMongoClient, Depends(get_mongo_client)]

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl='/login/access-token/')
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(request: Request, token: TokenDep) -> User:
    ok, data = parse_token(token)
    if not ok:
        raise HTTPException(status_code=403, detail='Could not validate credentials.')

    user = User(_id=data)
    request.state.user = user
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
