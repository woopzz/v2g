import datetime as dt
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from v2g.core.config import settings

JWT_ALGORITHM = 'HS256'

pwd_context = CryptContext(schemes=['bcrypt'])

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl='/login/access-token/')
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def create_token(sub):
    claims = {
        'sub': sub,
        'exp': (
            dt.datetime.now(dt.timezone.utc)
            + dt.timedelta(minutes=settings.jwt_lifetime_in_minutes)
        ),
    }
    access_token = jwt.encode(claims, settings.secret, algorithm=JWT_ALGORITHM)
    return access_token


def parse_token(token):
    try:
        claims = jwt.decode(token, settings.secret, algorithms=[JWT_ALGORITHM])
        return True, claims['sub']
    except jwt.PyJWTError:
        return False, None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)
