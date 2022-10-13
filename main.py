from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import sql_database, redis_db
from models.redis_tets import Test

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():

    await sql_database.connect()


@app.on_event("shutdown")
async def shutdown():

    await sql_database.disconnect()


@app.get("/")
async def root():
    return {"status": "Working"}


@app.get("/redis_test")
async def all():
    return [format(pk) for pk in Test.all_pks()]


def format(pk: str):
    test = Test.get(pk)

    return {"id": test.pk, "name": test.name, "quantity": test.quantity}


@app.post("/redis_test")
async def create(test: Test):
    return test.save()
