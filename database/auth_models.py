from typing import Optional

from pydantic import EmailStr
from sqlmodel import SQLModel


class UserLogin(SQLModel):
    email: EmailStr
    password: str


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    id: Optional[int] = None
