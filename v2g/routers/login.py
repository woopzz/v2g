import datetime as dt
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from v2g.models import Token
from v2g.config import settings
from .dependencies import MongoClientDep

router = APIRouter()

@router.post('/access-token')
async def get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    mongo_client: MongoClientDep,
) -> Token:
    username = form_data.username
    password = form_data.password

    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('users')

    result = await collection.find_one({'username': username})
    if not result or result['password'] != password:
        raise HTTPException(status_code=404, detail='Not found any user with these credentials.')

    user_id = result['_id']

    claims = {
        'sub': str(user_id),
        'exp': (
            dt.datetime.now(dt.timezone.utc)
            + dt.timedelta(minutes=settings.jwt_lifetime_in_minutes)
        ),
    }
    access_token = jwt.encode(claims, settings.secret, algorithm='HS256')
    return Token(access_token=access_token)
