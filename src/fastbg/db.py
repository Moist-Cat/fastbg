"""
ORM layer for the DB
"""
import functools
from datetime import datetime
import re

from sqlalchemy.orm import declarative_base, relationship, as_declarative, declared_attr
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Float,
    String,
    Text,
    ForeignKey,
    Column,
    Table,
)

from fastbg.conf import settings
from fastbg.auth.security import get_password_hash, verify_password

# Mixins
class TsMixin:
    """
    Adds created_at and updated_at
    """

    created_at = Column(DateTime, default=datetime.utcnow)
    # sqlalchemy has a convenient hook for auto-updates
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SoftDeleteMixin:
    """Mixin to add soft-delete functionality to models"""

    # since we will be doing this a lot might as well add an index
    is_soft_deleted = Column(Boolean, default=False, nullable=False, index=True)
    soft_deleted_at = Column(DateTime, nullable=True)

    def soft_delete(self):
        """Soft delete the instance"""
        self.is_soft_deleted = True
        self.soft_deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted instance"""
        self.is_soft_deleted = False
        self.soft_deleted_at = None


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


# decorator overrides metadata
Base.metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_`%(constraint_name)s`",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class PostTags(Base):
    post_id = Column(Integer, ForeignKey("post.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tag.id"), primary_key=True)


class User(Base, SoftDeleteMixin):
    name = Column(String(100), unique=True)
    pattern_name = re.compile(r"^[a-zA-Z0-9_]+$")
    password = Column(String(255), nullable=False)

    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan"
    )

    def set_password(self, password: str):
        self.password = get_password_hash(password)

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password)

    def __setattr__(self, name, value):
        if name == "password" and isinstance(value, str):
            self.set_password(value)
            return

        return super().__setattr__(name, value)

    def __init__(self, **kwargs):
        # avoid breaking the interface for this edge case
        password = kwargs.pop("password", None)
        super().__init__(**kwargs)
        if password:
            self.set_password(password)


class Post(Base, SoftDeleteMixin):
    title = Column(String(200), nullable=False, unique=True)
    content = Column(Text(10000), nullable=False)

    author_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    author = relationship("User", back_populates="posts")

    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    tags = relationship("Tag", secondary=PostTags.__table__, back_populates="posts")


class Comment(Base, SoftDeleteMixin):
    content = Column(Text, nullable=False)

    author_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    author = relationship("User", back_populates="comments")

    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    post = relationship("Post", back_populates="comments")

    # reply chains
    parent_comment_id = Column(Integer, ForeignKey("comment.id"), nullable=True)
    parent_comment = relationship(
        "Comment", remote_side="Comment.id", back_populates="replies"
    )
    replies = relationship(
        "Comment", back_populates="parent_comment", cascade="all, delete-orphan"
    )


# no need to include soft-delete bloat in tags
class Tag(Base):
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=True)

    posts = relationship("Post", secondary=PostTags.__table__, back_populates="tags")


async def create_db(name=settings.DATABASES["default"]["engine"]):
    engine = create_async_engine(name)
    await drop_db(name)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("INFO - Recreated database")
    await engine.dispose()


async def drop_db(name=settings.DATABASES["default"]["engine"]):
    engine = create_async_engine(name)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


def create_db_sync(name=settings.DATABASES["default"]["engine"]):
    engine = create_engine(name)
    drop_db_sync(name)

    Base.metadata.create_all(engine)

    print("INFO - Recreated database (sync)")
    return engine


def drop_db_sync(name=settings.DATABASES["default"]["engine"]):
    engine = create_engine(name)
    Base.metadata.drop_all(engine)
