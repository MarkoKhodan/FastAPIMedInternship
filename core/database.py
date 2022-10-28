from os import environ
import aioredis
import databases
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


host = environ.get("REDIS_HOST")
port = environ.get("REDIS_PORT")
password = environ.get("REDIS_PASSWORD")
redis_db = aioredis.from_url(f"redis://{host}:{port}/{password}", decode_responses=True)
