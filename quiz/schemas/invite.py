from pydantic import BaseModel


class InviteBase(BaseModel):
    id: int
    company: int
    user: int
