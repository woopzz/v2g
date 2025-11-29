from fastapi import HTTPException, Request
from slowapi import Limiter

from v2g.config import settings


def get_rate_limit_key(request: Request):
    user = getattr(request.state, 'user', None)
    if not user:
        raise HTTPException(status_code=500, detail='User is expected.')

    key = f'user:{user.id}'
    return key


limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=settings.get_rate_limit_dsn(),
    enabled=settings.rate_limit_enabled,
)
