import logging
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Type, Optional, Set, Dict

from fastbg.api import get_db, get_current_user
from fastbg.schema import sqlalchemy_to_pydantic
from fastbg.query import base_query, query_deleted
from fastbg.db import User

log = logging.getLogger("global")


class CrudEndpoint:
    LIST = "list"
    GET = "get"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESTORE = "restore"
    LIST_DELETED = "list_deleted"


def protected(func):
    """
    Protect methods against general exceptions
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException as e:
            raise
        except Exception as e:
            log.error("Error: %s", str(e))
            # rollback is done in api.py
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Operation failed"
            )

    return wrapper


def make_crud_router(
    model: Type,
    schema: Type = None,
    create_schema: Type = None,
    update_schema: Type = None,
    prefix: str = None,
    exclude_fields: List[str] = None,
    exclude_fields_create: List[str] = None,
    exclude_fields_update: List[str] = None,
    disabled: Dict[str, str] = None,
):
    enable_soft_delete = hasattr(model, "is_soft_deleted")
    exclude_fields = exclude_fields or []
    schema = schema or sqlalchemy_to_pydantic(model, exclude=exclude_fields)

    disabled = disabled or set()

    if create_schema is None:
        create_exclude = (exclude_fields_create or []) + [
            "id",
            "created_at",
            "updated_at",
        ]
        if enable_soft_delete:
            create_exclude.extend(["is_soft_deleted", "soft_deleted_at"])
        create_schema = sqlalchemy_to_pydantic(model, exclude=create_exclude)

    if update_schema is None:
        update_exclude = (exclude_fields_update or []) + [
            "id",
            "created_at",
            "updated_at",
        ]
        if enable_soft_delete:
            update_exclude.extend(["is_soft_deleted", "soft_deleted_at"])
        update_schema = sqlalchemy_to_pydantic(
            model, exclude=update_exclude, all_optional=True
        )

    prefix = prefix or f"/{model.__name__.lower()}"

    router = APIRouter(prefix=prefix)

    if not CrudEndpoint.LIST in disabled:

        @router.get("/", response_model=List[schema])
        @protected
        async def list_items(
            page: Optional[int] = 0,
            page_size: Optional[int] = 10,
            db: AsyncSession = Depends(get_db),
        ):
            limit = page_size
            offset = page * page_size
            result = await db.execute(base_query(model).offset(offset).limit(limit))
            items = result.scalars().all()
            return items

    if not CrudEndpoint.CREATE in disabled:

        @router.post("/", response_model=create_schema)
        @protected
        async def create_item(
            item: create_schema,
            db: AsyncSession = Depends(get_db),
            user: "User" = Depends(get_current_user),
        ):
            db_item = model(**item.dict())
            db.add(db_item)
            await db.commit()
            await db.refresh(db_item)
            return db_item

    if not CrudEndpoint.GET in disabled:

        @router.get("/{item_id}", response_model=schema)
        @protected
        async def get_item(
            item_id: int,
            db: AsyncSession = Depends(get_db),
        ):
            result = await db.execute(base_query(model).where(model.id == item_id))
            item = result.scalar_one_or_none()
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            return item

    if not CrudEndpoint.UPDATE in disabled:

        @router.put("/{item_id}", response_model=update_schema)
        @protected
        async def update_item(
            item_id: int,
            item: update_schema,
            db: AsyncSession = Depends(get_db),
            user: "User" = Depends(get_current_user),
        ):
            result = await db.execute(base_query(model).where(model.id == item_id))
            db_item = result.scalar_one_or_none()
            if not db_item:
                raise HTTPException(status_code=404, detail="Item not found")

            for field, value in item.dict(exclude_unset=True).items():
                setattr(db_item, field, value)

            await db.commit()
            await db.refresh(db_item)
            return db_item

    if not CrudEndpoint.DELETE in disabled:
        if not enable_soft_delete:

            @router.delete("/{item_id}")
            @protected
            async def delete_item(
                item_id: int,
                db: AsyncSession = Depends(get_db),
                user: "User" = Depends(get_current_user),
            ):
                result = await db.execute(base_query(model).where(model.id == item_id))
                db_item = result.scalar_one_or_none()
                if not db_item:
                    raise HTTPException(status_code=404, detail="Item not found")

                await db.delete(db_item)
                await db.commit()
                return {"message": "Item deleted successfully"}

        else:

            @router.delete("/{item_id}")
            @protected
            async def delete_item(
                item_id: int,
                hard: Optional[bool] = False,
                db: AsyncSession = Depends(get_db),
                user: "User" = Depends(get_current_user),
            ):
                result = await db.execute(base_query(model).where(model.id == item_id))
                db_item = result.scalar_one_or_none()
                if not db_item:
                    raise HTTPException(status_code=404, detail="Item not found")

                if not hard:
                    db_item.soft_delete()
                    await db.commit()
                    return {"message": "Item soft deleted successfully"}
                else:
                    await db.delete(db_item)
                    await db.commit()
                    return {"message": "Item deleted successfully"}

    # convenience endpoints
    if enable_soft_delete:
        if not CrudEndpoint.RESTORE in disabled:

            @router.post("/{item_id}/restore", response_model=schema)
            @protected
            async def restore_item(
                item_id: int,
                db: AsyncSession = Depends(get_db),
                user: "User" = Depends(get_current_user),
            ):
                stmt = select(model).where(model.id == item_id)
                result = await db.execute(stmt)
                db_item = result.scalar_one_or_none()
                if not db_item:
                    raise HTTPException(status_code=404, detail="Item not found")

                if not db_item.is_soft_deleted:
                    raise HTTPException(
                        status_code=400, detail="Item is not soft deleted"
                    )

                db_item.restore()
                await db.commit()
                await db.refresh(db_item)
                return db_item

        if not CrudEndpoint.LIST_DELETED in disabled:

            @router.get(
                "/deleted/",
                response_model=List[schema],
            )
            @protected
            async def list_deleted_items(
                page: Optional[int] = 0,
                page_size: Optional[int] = 10,
                db: AsyncSession = Depends(get_db),
                user: "User" = Depends(get_current_user),
            ):
                limit = page_size
                offset = page * page_size
                stmt = query_deleted(model).offset(offset).limit(limit)
                result = await db.execute(stmt)
                items = result.scalars().all()
                return items

    return router
