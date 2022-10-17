import logging
from typing import List
from sqlalchemy.orm import Session
from core.auth import Auth
from core.database import get_db
from core.hashing import Hasher
from quiz.models.user import User
from . import service
from fastapi import APIRouter, HTTPException, Depends, Security
from quiz.schemas.user import UserBase, UserCreate, UserUpdate, UserSignIn
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .service import create_user

router = APIRouter()

logger = logging.getLogger("quiz-logger")

security = HTTPBearer()
auth_handler = Auth()


@router.post("/login")
def login(user_details: UserSignIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=user_details.email).first()
    if user is None:
        return HTTPException(status_code=401, detail="Invalid email")
    if not Hasher.verify_password(user_details.password, user.password):
        return HTTPException(status_code=401, detail="Invalid password")

    token = auth_handler.encode_token(user.email)
    return {"token": token, "username": {user.username}, "email": {user.email}}


@router.get("/refresh_token")
def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    expired_token = credentials.credentials
    return auth_handler.refresh_token(expired_token)


@router.get("/{pk}", response_model=UserBase)
async def user_detail(pk):
    user = await service.get_detail_user(pk)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    logger.debug(f"User with id {pk} details displayed")
    return user


@router.get("/", response_model=List[UserBase])
async def user_list():
    logger.debug(f"User list displayed")
    return await service.get_user_list()


@router.post("/register", status_code=201, response_model=UserBase)
async def register(user_details: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=user_details.email).first()
    if user:
        return "Account already exists"

    if user_details.confirm_password == user_details.password:
        logger.debug(f"User created")
        return await create_user(user_details)
    else:
        return HTTPException(status_code=401, detail="Invalid password")


@router.put("/{pk}", status_code=201, response_model=UserBase)
async def user_update(pk: int, item: UserUpdate):
    user = await service.get_detail_user(pk)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    logger.debug(f"User with id {pk} updated")
    return await service.update_user(pk, item)


@router.delete("/{pk}", status_code=204)
async def user_delete(pk: int):
    user = await service.get_detail_user(pk)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        logger.debug(f"User with id {pk} deleted from database")
        await service.delete_user(pk)

