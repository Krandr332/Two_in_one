from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

from datetime import datetime
import random
import string

Base = declarative_base()


class URLMapping(Base):
    __tablename__ = "url_mappings"

    id = Column(Integer, primary_key=True, index=True)
    short_id = Column(String, unique=True, index=True, nullable=False)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    clicks = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    def __init__(self, original_url: str):
        self.original_url = original_url
        self.short_id = self.generate_short_id()

    @staticmethod
    def generate_short_id(length: int = 6) -> str:

        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))