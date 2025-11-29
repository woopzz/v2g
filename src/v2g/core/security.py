import datetime as dt

import jwt
from passlib.context import CryptContext

from v2g.core.config import settings
from v2g.core.models import Token

pwd_context = CryptContext(schemes=['bcrypt'])

JWT_ALGORITHM = 'HS256'


def create_token(sub):
    claims = {
        'sub': sub,
        'exp': (
            dt.datetime.now(dt.timezone.utc)
            + dt.timedelta(minutes=settings.jwt_lifetime_in_minutes)
        ),
    }
    access_token = jwt.encode(claims, settings.secret, algorithm=JWT_ALGORITHM)
    return Token(access_token=access_token)


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
