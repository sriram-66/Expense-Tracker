import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class ExpenseIn(BaseModel):
    amount: float = Field(gt=0, le=10_000_000)
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)
    date: dt.date


class ExpenseOut(ExpenseIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
