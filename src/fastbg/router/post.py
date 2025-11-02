from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastbg.router.core import make_crud_router, CrudEndpoint, protected
from fastbg.db import Post
from fastbg.schema import sqlalchemy_to_pydantic
from fastbg.auth.authorization import is_owner
from fastbg.api import get_db, get_current_user
from fastbg.query import base_query

router = make_crud_router(Post, disabled={CrudEndpoint.UPDATE, CrudEndpoint.DELETE})

update_schema = sqlalchemy_to_pydantic(
    Post,
    exclude=["id", "created_at", "updated_at", "is_soft_deleted", "soft_deleted_at"],
    all_optional=True,
)


@router.put("/{item_id}", response_model=update_schema)
@is_owner(Post, owner_field="author_id")
@protected
async def update_item(
    item_id: int,
    item: update_schema,
    db: AsyncSession = Depends(get_db),
    user: "User" = Depends(get_current_user),
):
    result = await db.execute(base_query(Post).where(Post.id == item_id))
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    for field, value in item.dict(exclude_unset=True).items():
        setattr(db_item, field, value)

    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
@is_owner(Post, owner_field="author_id")
@protected
async def delete_item(
    item_id: int,
    hard: Optional[bool] = False,
    db: AsyncSession = Depends(get_db),
    user: "User" = Depends(get_current_user),
):
    result = await db.execute(base_query(Post).where(Post.id == item_id))
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
