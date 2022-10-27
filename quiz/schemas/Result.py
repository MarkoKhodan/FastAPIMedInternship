from datetime import datetime

from pydantic import BaseModel


class ResultBase(BaseModel):
    id: int
    user: int
    company: int
    result: int
    quiz_id: int
    attempt: int
    average_result: float
    created_at: datetime
