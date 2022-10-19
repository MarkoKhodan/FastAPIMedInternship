import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import paginate, LimitOffsetPage, Page, add_pagination
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.database import database
from quiz.models.redis_tets import Test
from logging.config import dictConfig
from fastapi import FastAPI, Depends
from log_conf import log_config
from quiz.models.user import User
from quiz.schemas.user import UserBase
from routes import routes

dictConfig(log_config)
logger = logging.getLogger("quiz-logger")

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


def get_db():
    db = SessionLocal
    try:
        yield db
    finally:
        db.close()


# LIST WITH PAGINATION
@app.get("/users", response_model=Page[UserBase])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserBase])
def get_blogs(db: Session = Depends(get_db)):
    logger.debug(f"User list displayed")
    return paginate(db.query(User).all())


add_pagination(app)


app.include_router(routes)


@app.get("/")
async def root():
    logger.debug("Root is called")
    return {"status": "Working"}


@app.get("/redis_test")
async def all():
    return [format(pk) for pk in Test.all_pks()]


def format(pk: str):
    test = Test.get(pk)
    return {"id": test.pk, "name": test.name, "quantity": test.quantity}


@app.post("/redis_test")
async def create(test: Test):
    logger.debug("This added")
    return test.save()
