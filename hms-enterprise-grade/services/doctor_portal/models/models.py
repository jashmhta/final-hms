import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class EncryptedString(String):
    pass


class UserStub(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
