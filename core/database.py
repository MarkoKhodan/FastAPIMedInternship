from os import environ

import databases
from redis_om import get_redis_connection
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_USER = environ.get("DB_USER", "marko")
DB_HOST = environ.get("DB_HOST", "localhost")
DB_NAME = environ.get("DB_NAME", "marko")
DB_PASSWORD = environ.get("DB_PASSWORD", "")
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"


engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
database = databases.Database(SQLALCHEMY_DATABASE_URL)

redis_db = get_redis_connection(
    host=environ.get("REDIS_HOST"),
    port=environ.get("REDIS_PORT"),
    password=environ.get("REDIS_PASSWORD"),
    decode_responses=True,
)
