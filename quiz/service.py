
from random import randint

from fastapi import Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from core.auth import Auth
from core.hashing import Hasher
from utils import VerifyToken
from .schemas.user import UserCreate, UserUpdate
from core.database import database, get_db
from quiz.models.user import users, User

security = HTTPBearer()
auth_handler = Auth()



def get_data(page: int = 0, limit: int = 50):

    data = database.fetch_all(query=users.select().offset(page).limit(limit))
    return data


async def get_user_list():
    user_list = await database.fetch_all(query=users.select())

    return [dict(result) for result in user_list]


async def get_detail_user(pk: int):
    user = await database.fetch_one(query=users.select().where(users.c.id == int(pk)))
    if user is not None:
        user = dict(user)
        return user
    return None


h
async def create_user(user_details: UserCreate):
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



async def update_user(pk: int, item: UserUpdate):
    post = users.update().where(users.c.id == pk).values(**item.dict())
    await database.execute(post)
    return {**item.dict(), "id": pk}


async def delete_user(pk: int):
    user = users.delete().where((users.c.id == pk))
    return await database.execute(user)



async def authorize_check(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
):
    authorized = False

    auth_token = VerifyToken(credentials.credentials).verify()
    email = auth_token.get("https://example.com/email")
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
    elif auth_handler.decode_token(jwt_token):
        authorized = True

    return authorized
