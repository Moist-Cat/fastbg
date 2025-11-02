from datetime import timedelta
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from fastbg.router.core import make_crud_router, CrudEndpoint, protected
from fastbg.db import User, Post, Comment
from fastbg.api import get_db
from fastbg.auth.security import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from fastbg.query import base_query
from fastbg.schema import sqlalchemy_to_pydantic


class Token(BaseModel):
    access_token: str
    token_type: str


router = make_crud_router(
    User, exclude_fields=["password"], disabled={CrudEndpoint.CREATE}
)


create_schema = sqlalchemy_to_pydantic(
    User,
    exclude=["id", "created_at", "updated_at", "is_soft_deleted", "soft_deleted_at"],
)

post_schema = sqlalchemy_to_pydantic(
    Post,
)

comment_schema = sqlalchemy_to_pydantic(
    Comment,
)

# no auth
@router.post("/", response_model=create_schema)
@protected
async def create_item(
    item: create_schema,
    db: AsyncSession = Depends(get_db),
):
    db_item = User(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.get("/{item_id}/posts", response_model=List[post_schema])
@protected
async def list_posts(
    item_id: int,
    page: Optional[int] = 0,
    page_size: Optional[int] = 10,
    db: AsyncSession = Depends(get_db),
):
    limit = page_size
    offset = page * page_size
    result = await db.execute(
        base_query(Post).where(item_id == Post.author_id).offset(offset).limit(limit)
    )
    items = result.scalars().all()
    return items


@router.get("/{item_id}/comments", response_model=List[comment_schema])
@protected
async def list_comments(
    item_id: int,
    page: Optional[int] = 0,
    page_size: Optional[int] = 10,
    db: AsyncSession = Depends(get_db),
):
    limit = page_size
    offset = page * page_size
    result = await db.execute(
        base_query(Comment)
        .where(item_id == Comment.author_id)
        .offset(offset)
        .limit(limit)
    )
    items = result.scalars().all()
    return items


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(base_query(User).where(User.name == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.name}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
