from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from v2g.models import Token
from v2g.config import settings
from v2g.security import create_token, verify_password
from .dependencies import MongoClientDep
from .utils import create_error_responses

router = APIRouter()

@router.post(
    path='/access-token',
    response_model=Token,
    summary='Create new token',
    responses=create_error_responses({404}),
)
async def get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    mongo_client: MongoClientDep,
):
    username = form_data.username
    password = form_data.password

    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('users')

    result = await collection.find_one({'username': username})
    if not (result and verify_password(password, result['password'])):
        raise HTTPException(status_code=404, detail='Not found any user with these credentials.')

    user_id = result['_id']
    return create_token(str(user_id))
