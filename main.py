import logging
from fastapi.middleware.cors import CORSMiddleware
from core.database import database, redis_db
from logging.config import dictConfig
from fastapi import FastAPI
from core.log_conf import log_config
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
    await redis_db.close()

app.include_router(routes)

@router.get(
    "/test_pipeline",
    status_code=status.HTTP_200_OK,
)
async def test_pipeline():
    return {"status": "woeking"
