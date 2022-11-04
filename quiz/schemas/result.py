from datetime import datetime

from pydantic import BaseModel


class ResultBase(BaseModel):
    id: int
    user: int
    company: int
    result: int
    quiz_id: int
    attempts: int
    average_result: float
    created_at: datetime


class QuizResultAvarage(BaseModel):
    user_id: int
    average_result: float
    created_at: datetime


class UserResultAvarage(BaseModel):
    quiz_id: int
    average_result: float
    created_at: datetime


class UserQuizResultAvarage(BaseModel):
    average_result: float
    created_at: datetime


class UserQuizLastActivity(BaseModel):
    quiz_id: int
    last_activity: datetime
