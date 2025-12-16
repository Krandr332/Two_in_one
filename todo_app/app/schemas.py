from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# TodoItem schemas
class TodoItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False


class TodoItemCreate(TodoItemBase):
    pass


class TodoItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class TodoItem(TodoItemBase):
    id: int
    owner_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True