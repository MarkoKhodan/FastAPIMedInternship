from typing import Optional

from pydantic import BaseModel, conlist, validator

from quiz.schemas.questions import QuestionCreate, QuestionRead, QuestionPass


def validate_question(questions: conlist(QuestionCreate)) -> conlist(QuestionCreate):
    assert len(questions) >= 2, "You should have more than 2 questions in one quiz"
    return questions


class QuizBase(BaseModel):
    id: int
    title: str
    description: str
    passing_frequency: int
    company: int


class QuizList(BaseModel):
    id: int
    title: str
    description: str
    passing_frequency: Optional[int]
    company: int


class QuizCreate(BaseModel):
    id: int
    title: str
    description: str
    questions: conlist(QuestionCreate, min_items=2)

    @validator("questions", pre=True)
    def questions_is_valid(
        cls, questions: conlist(QuestionCreate)
    ) -> conlist(QuestionCreate):
        return validate_question(questions)


class QuizUpdate(BaseModel):
    id: int
    title: str
    description: str
    questions: conlist(QuestionCreate, min_items=2)

    @validator("questions", pre=True)
    def questions_is_valid(
        cls, questions: conlist(QuestionCreate)
    ) -> conlist(QuestionCreate):
        return validate_question(questions)


class QuizRead(BaseModel):
    id: int
    title: str
    description: str
    questions: conlist(QuestionRead)


class QuizPass(BaseModel):
    answers: list[QuestionPass]
