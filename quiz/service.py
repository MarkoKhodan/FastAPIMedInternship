from .schemas.user import UserCreate, UserUpdate
from core.database import database
from quiz.models.user import users


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


async def create_user(item: UserCreate):
    post = users.insert().values(**item.dict())
    pk = await database.execute(post)
    return {**item.dict(), "id": pk}


async def update_user(pk: int, item: UserUpdate):
    post = users.update().where(users.c.id == pk).values(**item.dict())
    await database.execute(post)
    return {**item.dict(), "id": pk}


async def delete_user(pk: int):
    user = users.delete().where((users.c.id == pk))
    return await database.execute(user)
