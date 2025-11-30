from typing import Annotated

from fastapi import Depends, Request

from v2g.core.database import MongoClientDep
from v2g.core.repository import BaseRepository
from v2g.core.security import get_password_hash, verify_password

from .models import User


class UserRepository(BaseRepository):
    def get_users_collection(self):
        return self.get_database().get_collection('users')

    async def get_by_id(self, id_):
        users_coll = self.get_users_collection()
        user = await users_coll.find_one({'_id': id_})
        return user and User(**user)

    async def get_by_username(self, username):
        users_coll = self.get_users_collection()
        user = await users_coll.find_one({'username': username})
        return user and User(**user)

    async def create(self, username, password):
        users_coll = self.get_users_collection()
        create_values = {
            username: username,
            password: get_password_hash(password),
        }
        result = await users_coll.insert_one(create_values)
        return result.inserted_id

    async def verify_password(self, user, password):
        return verify_password(password, user.password)


async def get_user_repository(request: Request, mongo_client: MongoClientDep):
    return UserRepository(request=request, mongo_client=mongo_client)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
