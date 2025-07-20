from v2g.config import settings
from v2g.security import get_password_hash

async def create_user(username, password, mongo_client):
    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('users')
    result = await collection.insert_one({
        'username': username,
        'password': get_password_hash(password),
    })
    return result.inserted_id

async def delete_user(username, mongo_client):
    db = mongo_client.get_database(settings.mongodb.dbname)
    collection = db.get_collection('users')
    await collection.delete_many({'username': username})
