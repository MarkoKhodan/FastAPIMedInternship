import os
from functools import wraps
from random import randint
import jwt
from fastapi import Security, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from core.auth import Auth
from core.hashing import Hasher
from utils import VerifyToken
from .schemas.user import UserCreate, UserUpdate, UserSignIn
from core.database import database, get_db
from quiz.models.user import users, User


class UserService():
    security = HTTPBearer()
    auth_handler = Auth()

    @staticmethod
    def get_data(page: int = 0, limit: int = 50):
        data = database.fetch_all(query=users.select().offset(page).limit(limit))
        return data

    @staticmethod
    async def get_user_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> [dict]:
        user_list = db.query(User).offset(skip).limit(limit).all()

        return user_list

    @staticmethod
    async def get_detail_user(pk: int) -> dict:
        user = await database.fetch_one(query=users.select().where(users.c.id == int(pk)))
        if user is not None:
            user = dict(user)
            return user

    @staticmethod
    async def create_user(user_details: UserCreate) -> dict:
        hashed_password = Hasher.get_password_hash(user_details.password)
        user_details.password = hashed_password
        post = users.insert().values(
            username=user_details.username,
            email=user_details.email,
            password=user_details.password,
        )
        pk = await database.execute(post)
        return {
            "status": "user successfully added",
            "username": user_details.username,
            "email": user_details.email,
            "id": pk,
        }

    @staticmethod
    async def update_user(pk: int, user_details: UserUpdate):
        hashed_password = Hasher.get_password_hash(user_details.password)
        user_details.password = hashed_password
        post = users.update().where(users.c.id == pk).values(**user_details.dict())
        await database.execute(post)
        return {**user_details.dict(), "id": pk}

    @staticmethod
    async def delete_user(pk: int):
        user = users.delete().where((users.c.id == pk))
        return await database.execute(user)

    @staticmethod
    async def get_current_user_email(
            credentials: HTTPAuthorizationCredentials = Security(security),
    ) -> dict:
        auth_token = VerifyToken(credentials.credentials).verify()
        email = auth_token.get("email")
        secret = os.getenv("APP_SECRET_STRING")
        if email:
            return email

        else:
            algoritm = os.getenv("ALGORITHMS")
            payload = jwt.decode(
                credentials, secret, algorithms=[algoritm], verify_signature=False
            )
            return payload.get("email")


    @staticmethod
    def get_user_by_email(email, db: Session = Depends(get_db)):
        user = db.query(User).filter_by(email=email).first()
        return user



def auth_required(func):
    @wraps(func)
    async def wrapper(credentials: HTTPAuthorizationCredentials = Security(UserService.security),
                          db: Session = Depends(get_db), *args, **kwargs):

        authorized = False
        auth_token = VerifyToken(credentials.credentials).verify()
        email = auth_token.get("email")
        jwt_token = credentials.credentials
        if email:
            user = db.query(User).filter_by(email=email).first()
            if user:
                authorized = True
            else:
                user_details = {
                    "username": email,
                    "email": email,
                    "password": str(randint(1000000, 9999999)),
                }
                post = users.insert().values(
                    username=user_details["username"],
                    email=user_details["email"],
                    password=Hasher.get_password_hash(user_details["password"]),
                )
                await database.execute(post)
                authorized = True
        elif UserService.auth_handler.decode_token(jwt_token):

            authorized = True
        if authorized is not True:
            return HTTPException(status_code=401, detail="Invalid token")
        return await func(credentials, db, *args, **kwargs)

    return wrapper