from pydantic import BaseModel
from typing import Optional


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

    class Config:
        from_attributes = True