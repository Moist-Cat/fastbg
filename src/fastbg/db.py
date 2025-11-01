"""
ORM layer for the DB
"""
import functools
from datetime import datetime
import re

from sqlalchemy.orm import declarative_base, relationship, as_declarative, declared_attr
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import DateTime, Integer, Float, String, Text, ForeignKey, Column, Table

from fastbg.conf import settings

# Mixins
class TsMixin:
    """
    Adds created_at and updated_at
    """

    created_at = Column(DateTime, default=datetime.now)
    # sqlalchemy has a convenient hook for auto-updates
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


@as_declarative()
class Base(TsMixin):
    @declared_attr
    def __tablename__(cls):
        cls_name = cls.__name__
        table_name = list(cls_name)
        # PascalCase to snake_case
        for index, match in enumerate(re.finditer("[A-Z]", cls_name[1:])):
            table_name.insert(match.end() + index, "_")
        return "".join(table_name).lower()

    def as_dict(self):
        return {
            column: getattr(self, column) for column in self.__table__.columns.keys()
        }

    id = Column(Integer, primary_key=True)

    def __str__(self):
        return f"[{self.__class__.__name__}] ({self.as_dict()})"

    def __repr__(self):
        return self.__str__()


class User(Base):
    name = Column(String, default="Anonymous")


class Post(Base):
    content = String()

async def create_db(name=settings.DATABASES["default"]["engine"]):
    engine = create_async_engine(name)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("INFO - Created tables")
    await async_engine.dispose()

async def drop_db(name=settings.DATABASES["default"]["engine"]):
    engine = create_async_engine(name)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
