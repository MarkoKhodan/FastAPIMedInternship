from pydantic import BaseModel


class RequestBase(BaseModel):
    id: int
    company: int
    user: int
