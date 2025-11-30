from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from v2g.core.security import create_token
from v2g.core.utils import create_error_responses
from v2g.modules.users.repositories import UserRepositoryDep

from .models import Token

router = APIRouter()


@router.post(
    path='/access-token/',
    response_model=Token,
    summary='Create new token',
    responses=create_error_responses({404}),
)
async def get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo: UserRepositoryDep,
):
    username = form_data.username
    password = form_data.password

    user = await user_repo.get_by_username(username)
    if not (user and await user_repo.verify_password(user, password)):
        raise HTTPException(status_code=404, detail='Not found any user with these credentials.')

    access_token = create_token(str(user.id))
    return Token(access_token=access_token)
