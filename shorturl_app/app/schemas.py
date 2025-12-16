from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


class URLBase(BaseModel):
    url: str


class URLCreate(URLBase):
    pass


class URLInfo(BaseModel):
    short_id: str
    original_url: str
    created_at: datetime
    clicks: int
    short_url: str

    class Config:
        from_attributes = True


class URLStats(BaseModel):
    short_id: str
    original_url: str
    created_at: datetime
    clicks: int
    is_active: bool

    class Config:
        from_attributes = True