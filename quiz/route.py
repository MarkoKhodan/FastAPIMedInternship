import logging
from typing import List
from . import service
from fastapi import APIRouter, HTTPException, Depends
from quiz.schemas.user import UserBase, UserCreate, UserUpdate


router = APIRouter()

logger = logging.getLogger("quiz-logger")


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


@router.post("/", status_code=201, response_model=UserBase)
async def user_create(item: UserCreate):
    logger.debug(f"User created")
    return await service.create_user(item)


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
    logger.debug(f"User with id {pk} deleted from database")
    return user
