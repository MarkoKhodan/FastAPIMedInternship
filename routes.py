from fastapi import APIRouter
from quiz import user_routes, company_routes


routes = APIRouter()

routes.include_router(user_routes.router, prefix="/user")
routes.include_router(company_routes.router, prefix="/company")
