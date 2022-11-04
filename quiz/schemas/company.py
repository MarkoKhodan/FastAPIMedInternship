from datetime import datetime

from pydantic import BaseModel


class CompanyBase(BaseModel):
    id: int
    name: str
    description: str
    visibility: bool
    owner: int
    employees: list[int]


class CompanyList(BaseModel):
    id: int
    name: str
    description: str
    owner: int


class CompanyCreated(BaseModel):
    id: int
    name: str
    description: str
    owner: int


class CompanyCreate(BaseModel):
    name: str
    description: str


class CompanyUpdate(BaseModel):
    name: str
    description: str
    visibility: bool


class CompanyUpdated(BaseModel):
    id: int
    name: str
    description: str
    owner: int
    visibility: bool


class CompanyUserLastActivity(BaseModel):
    user_id: int
    last_activity: datetime
