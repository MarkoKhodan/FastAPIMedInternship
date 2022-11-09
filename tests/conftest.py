import datetime
from typing import Any
from typing import Generator


import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os

from core.auth import Auth
from main import app
from core.database import Base, get_db
from quiz.models.db_models import Company, Quiz, Question, Answer, User, Request, Result

auth_handler = Auth()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# this is to include backend dir in sys.path so that we can import from db,main.py


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
# Use connect_args parameter only with sqlite
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def app(app=app) -> Generator[FastAPI, Any, None]:
    """
    Create a fresh database on each test case.
    """
    Base.metadata.create_all(engine)  # Create the tables.
    _app = app
    yield _app
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(app: FastAPI) -> Generator[SessionTesting, Any, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionTesting(bind=connection)
    yield session  # use the session in tests.
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(
    app: FastAPI, db_session: SessionTesting
) -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def user(db_session):
    user = User(
        email="user@example.com",
        password="test_password",
        username="string",
        average_result=0,
    )
    db_session.add(user)
    db_session.commit()
    yield user


@pytest.fixture()
def token(user):
    token = auth_handler.encode_token(user.email)
    yield token


@pytest.fixture()
def company(db_session, user):
    company = Company(
        name="test",
        description="test_descr",
        owner=1,
    )
    db_session.add(company)
    db_session.commit()
    yield company


@pytest.fixture()
def test_request(db_session, user, company):
    request = Request(company=1, user=1)
    db_session.add(request)
    db_session.commit()
    yield request


@pytest.fixture()
def quiz(db_session, company):
    quiz = Quiz(title="test", description="test_descr", company_id=1)
    db_session.add(quiz)
    db_session.commit()

    question_1 = Question(question_title="test1", quiz_id="1")
    db_session.add(question_1)
    db_session.commit()
    question_2 = Question(question_title="test2", quiz_id="1")
    db_session.add(question_2)
    db_session.commit()

    correct_answer_1 = Answer(answer_text="test", is_correct=True, question_id=1)

    db_session.add(correct_answer_1)
    db_session.commit()

    wrong_answer_1 = Answer(answer_text="test", is_correct=False, question_id=1)

    db_session.add(wrong_answer_1)
    db_session.commit()

    correct_answer_2 = Answer(answer_text="test", is_correct=True, question_id=2)

    db_session.add(correct_answer_2)
    db_session.commit()

    wrong_answer_2 = Answer(answer_text="test", is_correct=False, question_id=2)

    db_session.add(wrong_answer_2)
    db_session.commit()

    yield quiz


@pytest.fixture()
def result(user, company, quiz, db_session):
    result = Result(
        user_id=user.id,
        company_id=company.id,
        quiz_id=quiz.id,
        result=75,
        correct_answers=2,
        attempts=2,
        average_result=50,
    )
    db_session.add(result)
    db_session.commit()

    yield result


FAKE_NOW = datetime.datetime(2012, 12, 12, 12, 12, 12)


@pytest.fixture()
def datetime_now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
