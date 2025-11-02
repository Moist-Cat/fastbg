"""
Various authorization recipes can be found here
"""
from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Callable, Optional, Union, List

from fastbg.api import get_current_user, get_db
from fastbg.db import User
from fastbg.query import base_query


class BaseAuthorizer:
    async def check(self, user: User, *args, **kwargs) -> bool:
        raise NotImplementedError("Subclasses must implement check method")


class OwnerAuthorizer(BaseAuthorizer):
    def __init__(
        self, model_class, id_param: str = "item_id", owner_field: str = "user_id"
    ):
        self.model_class = model_class
        self.id_param = id_param
        self.owner_field = owner_field

    async def check(self, user: User, db: AsyncSession, **kwargs) -> bool:
        item_id = kwargs.get(self.id_param)
        if not item_id:
            return False

        result = await db.execute(
            base_query(self.model_class).where(self.model_class.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return False

        return getattr(item, self.owner_field, None) == user.id


async def authorize(
    authorizer: BaseAuthorizer,
    kwargs: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    is_authorized = await authorizer.check(**kwargs)
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to perform this action",
        )
    return current_user


def is_owner(model_class, id_param: str = "item_id", owner_field: str = "user_id"):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            authorizer = OwnerAuthorizer(model_class, id_param, owner_field)
            await authorize(authorizer, kwargs)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
