from typing import Annotated

import bson
from fastapi import Depends, HTTPException, Query, Request, WebSocket

from v2g.core.security import TokenDep, parse_token


def _get_user_id_from_token(token: str) -> bson.ObjectId:
    ok, data = parse_token(token)
    if not ok:
        raise HTTPException(status_code=403, detail='Could not validate credentials.')
    user_id = bson.ObjectId(data)
    return user_id


def get_current_user_id(request: Request, token: TokenDep):
    user_id = _get_user_id_from_token(token)
    request.state.user_id = user_id
    return user_id


def get_current_user_id_ws(websocket: WebSocket, token: str = Query(...)):
    user_id = _get_user_id_from_token(token)
    websocket.state.user_id = user_id
    return user_id


CurrentUserIDDep = Annotated[bson.ObjectId, Depends(get_current_user_id)]
WsCurrentUserIDDep = Annotated[bson.ObjectId, Depends(get_current_user_id_ws)]
