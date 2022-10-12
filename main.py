import logging
from fastapi.middleware.cors import CORSMiddleware
from quiz.models.redis_tets import Test
from logging.config import dictConfig
from fastapi import FastAPI
from log_conf import log_config

dictConfig(log_config)
logger = logging.getLogger("quiz-logger")

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    logger.debug("Root is called")
    return {"status": "Working"}


@app.get("/redis_test")
async def all():
    return [format(pk) for pk in Test.all_pks()]


def format(pk: str):

    test = Test.get(pk)
    return {"id": test.pk, "name": test.name, "quantity": test.quantity}


@app.post("/redis_test")
async def create(test: Test):
    logger.debug("This added")
    return test.save()
