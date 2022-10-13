from os import environ

import databases
from redis_om import get_redis_connection

DB_USER = environ.get("DB_USER", "user")
DB_PASSWORD = environ.get("DB_PASSWORD", "password")
DB_HOST = environ.get("DB_HOST", "localhost")
DB_NAME = "api"
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
)

sql_database = databases.Database(SQLALCHEMY_DATABASE_URL)

redis_db = get_redis_connection(
    host=environ.get("REDIS_HOST"),
    port=environ.get("REDIS_PORT"),
    password=environ.get("REDIS_PASSWORD"),
    decode_responses=True,
)
