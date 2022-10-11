from redis_om import HashModel

from database import redis_db


class Test(HashModel):
    name: str
    quantity: int

    class Meta:
        database = redis_db
