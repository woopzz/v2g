from fastapi import APIRouter, HTTPException

from v2g.models import UserPublic, UserCreate
from v2g.config import settings
from .dependencies import MongoClientDep, CurrentUser

router = APIRouter()

@router.get('/me', response_model=UserPublic)
async def get_my_user(current_user: CurrentUser, mongo_client: MongoClientDep):
    db = mongo_client.get_database(settings.mongodb.dbname)
    collection_users = db.get_collection('users')

    user = await collection_users.find_one({'_id': current_user.id})
    if not user:
        raise HTTPException(status_code=404)

    collection_conversions = db.get_collection('conversions')
    conversions = [x async for x in collection_conversions.find({'owner_id': current_user.id})]

    return UserPublic(
        _id=current_user.id,
        username=user['username'],
        conversions=conversions,
    )

@router.post('/', response_model=UserPublic)
async def create_user(create_data: UserCreate, mongo_client: MongoClientDep):
    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('users')

    result = await collection.find_one({'username': create_data.username})
    if result:
        raise HTTPException(status_code=400, detail='This username is already taken.')

    user = create_data.model_dump()
    result = await collection.insert_one(user)
    user_id = result.inserted_id

    return {
        '_id': user_id,
        'username': user['username'],
        'conversions': [],
    }
