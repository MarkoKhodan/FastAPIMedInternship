import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from sqlalchemy.orm import Session
from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials
from core.database import get_db
from core.database import database
from logging.config import dictConfig
from fastapi import FastAPI, Depends
from core.log_conf import log_config
from quiz.service import UserService, auth_required
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
@auth_required
async def private(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
):

    return {"message": "This is private endpoint"}


add_pagination(app)
app.include_router(routes)
