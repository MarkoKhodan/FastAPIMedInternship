from pydantic import BaseModel


class AnswerBase(BaseModel):
    id: int
    answer_text: str
    is_correct: bool
    question_id: int


class AnswerCreate(BaseModel):
    answer_text: str
    is_correct: bool
