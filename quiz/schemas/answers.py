from pydantic import BaseModel


class AnswerBase(BaseModel):
    id: int
    answer_text: str
    is_correct: bool
    question: int


class AnswerCreate(BaseModel):
    answer_text: str
    is_correct: bool
