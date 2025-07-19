from typing import Annotated

import jwt
from fastapi import Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pymongo import AsyncMongoClient

from v2g.models import User
from v2g.config import settings

async def get_mongo_client(request: Request):
    return request.state.mongo_client

MongoClientDep = Annotated[AsyncMongoClient, Depends(get_mongo_client)]

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl='/login/access-token')
TokenDep = Annotated[str, Depends(reusable_oauth2)]

def get_current_user(token: TokenDep) -> User:
    try:
        claims = jwt.decode(token, settings.secret, algorithms=['HS256'])
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail='Could not validate credentials.')

    return User(_id=claims['sub'])

CurrentUser = Annotated[User, Depends(get_current_user)]
