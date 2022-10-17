import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import paginate, LimitOffsetPage, Page, add_pagination
from sqlalchemy.orm import Session
from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials
from core.database import get_db
from core.database import database
from logging.config import dictConfig
from fastapi import FastAPI, Depends
from log_conf import log_config
from quiz.models.user import User
from quiz.schemas.user import UserBase
from quiz.service import security, authorize_check
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


@app.get("/api/private")
async def private(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
):
    """A valid access token is required to access this route"""
    if await authorize_check(credentials=credentials, db=db) is not True:
        return await authorize_check(credentials=credentials, db=db)

    else:
        return {"message": "This is private endpoint"}


# LIST WITH PAGINATION
@app.get("/users", response_model=Page[UserBase])
@app.get("/users/limit-offset", response_model=LimitOffsetPage[UserBase])
def get_users(db: Session = Depends(get_db)):
    logger.debug(f"User list displayed")
    return paginate(db.query(User).all())


add_pagination(app)
app.include_router(routes)
