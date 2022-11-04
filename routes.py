from fastapi import APIRouter
from quiz import user_routes, company_routes, quiz_routes, analytics_routes

routes = APIRouter()

routes.include_router(user_routes.router, prefix="/user")
routes.include_router(company_routes.router, prefix="/company")
routes.include_router(quiz_routes.router, prefix="/quiz")
routes.include_router(analytics_routes.router, prefix="/analytic")
