from v2g.core.config import settings
from v2g.core.security import create_token, get_password_hash
from v2g.modules.auth.models import Token


async def create_user(username, password, mongo_client):
    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('users')
    result = await collection.insert_one(
        {
            'username': username,
            'password': get_password_hash(password),
        }
    )
    return result.inserted_id


async def delete_user(username, mongo_client):
    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('users')
    await collection.delete_many({'username': username})


async def create_user_and_token(mongo_client, username='test', password='testtest'):
    user_id = await create_user(username, password, mongo_client)
    access_token = create_token(str(user_id))
    token = Token(access_token=access_token)
    return user_id, token
