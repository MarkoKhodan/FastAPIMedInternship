from fastapi import APIRouter
from quiz import route


routes = APIRouter()

routes.include_router(route.router, prefix="/user")
