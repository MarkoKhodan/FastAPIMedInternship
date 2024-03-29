import string
from typing import Optional

from pydantic import BaseModel, EmailStr, constr, validator


def validate_username(username: str) -> str:
    allowed = string.ascii_letters + string.digits + "-" + "_"
    assert all(char in allowed for char in username), "Invalid characters in username."
    assert len(username) >= 3, "Username must be 3 characters or more."
    return username


class UserBase(BaseModel):

    id: int
    password: constr(min_length=7, max_length=100)
    email: EmailStr
    username: str


class UserInfo(BaseModel):
    id: int
    email: EmailStr
    username: str



class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=7, max_length=100)
    confirm_password: constr(min_length=7, max_length=100)
    username: str

    @validator("username", pre=True)
    def username_is_valid(cls, username: str) -> str:
        return validate_username(username)


class UserUpdate(BaseModel):
    username: Optional[str]
    password: Optional[constr(min_length=7, max_length=100)]

    @validator("username", pre=True)
    def username_is_valid(cls, username: str) -> str:
        return validate_username(username)


class UserSignIn(BaseModel):
    email: EmailStr
    password: constr(min_length=7, max_length=100)


class UserLogIn(BaseModel):
    token: str
    username: str
    email: EmailStr


class UserCreated(BaseModel):
    username: str
    email: EmailStr
    id: int


class UserDelete(BaseModel):
    pass


class UserAverageResult(BaseModel):
    user_id: int
    average_result: float
