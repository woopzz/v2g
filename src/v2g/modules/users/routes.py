from fastapi import APIRouter, HTTPException

from v2g.core.utils import create_error_responses
from v2g.modules.conversions.repositories import ConversionRepositoryDep

from .dependencies import CurrentUserIDDep
from .models import UserCreate, UserPublic
from .repositories import UserRepositoryDep

router = APIRouter()


@router.get(
    path='/me/',
    response_model=UserPublic,
    summary='Get info of my user',
    responses=create_error_responses({404}, add_token_related_errors=True),
)
async def get_my_user(
    current_user_id: CurrentUserIDDep,
    user_repo: UserRepositoryDep,
    convsersion_repo: ConversionRepositoryDep,
):
    user = await user_repo.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404)

    conversions = [x async for x in await convsersion_repo.get(owner_id=current_user_id, many=True)]

    return {
        '_id': current_user_id,
        'username': user.username,
        'conversions': conversions,
    }


@router.post(
    path='/',
    response_model=UserPublic,
    summary='Create new user',
    responses=create_error_responses({400}),
)
async def create_user(create_data: UserCreate, user_repo: UserRepositoryDep):
    existing_user = await user_repo.get_by_username(create_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail='This username is already taken.')

    user_id = await user_repo.create(username=create_data.username, password=create_data.password)
    return {
        '_id': user_id,
        'username': create_data.username,
        'conversions': [],
    }
