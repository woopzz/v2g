from typing import Annotated

import bson
from fastapi import Depends, HTTPException, Request

from v2g.core.security import TokenDep, parse_token


def get_current_user_id(request: Request, token: TokenDep):
    ok, data = parse_token(token)
    if not ok:
        raise HTTPException(status_code=403, detail='Could not validate credentials.')

    user_id = bson.ObjectId(data)
    request.state.user_id = user_id
    return user_id


CurrentUserIDDep = Annotated[bson.ObjectId, Depends(get_current_user_id)]
