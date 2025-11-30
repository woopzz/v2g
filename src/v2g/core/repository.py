from v2g.core.config import settings


class BaseRepository:
    def __init__(self, *, request, mongo_client):
        self.request = request
        self.mongo_client = mongo_client

    def get_database(self):
        return self.mongo_client.get_database(settings.mongodb.dbname)
