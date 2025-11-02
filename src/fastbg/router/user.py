from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from fastbg.router.core import make_crud_router, CrudEndpoint, protected
from fastbg.db import User
from fastbg.api import get_db, get_current_user
from fastbg.auth.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from fastbg.db import User
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
