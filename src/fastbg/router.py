from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Type, Any
from functools import wraps
import logging

from fastbg.api import get_db
from fastbg.schema import sqlalchemy_to_pydantic

log = logging.getLogger("global")

def protected(func):
    """
    Protect methods against general exceptions
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            log.error(f"Error: {e}")
            # rollback is done in api.py
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Operation failed"
            )
    return wrapper

def make_crud_router(
    model: Type,
    schema: Type = None,
    create_schema: Type = None,
    update_schema: Type = None,
    prefix: str = None,
    tags: List[str] = None
):
    schema = schema or sqlalchemy_to_pydantic(model)
    create_schema = create_schema or schema
    update_schema = update_schema or schema
    prefix = prefix or f"/{model.__name__.lower()}"
    
    router = APIRouter(prefix=prefix)

    @router.get("/", response_model=List[schema])
    @protected
    async def list_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(model))
        items = result.scalars().all()
        return items
    
    @router.post("/", response_model=schema)
    @protected
    async def create_item(item: create_schema, db: AsyncSession = Depends(get_db)):
        db_item = model(**item.dict())
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item
    
    @router.get("/{item_id}", response_model=schema)
    @protected
    async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
        result = await db.execute(
            select(model).where(model.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item
    
    @router.put("/{item_id}", response_model=schema)
    @protected
    async def update_item(item_id: int, item: update_schema, db: AsyncSession = Depends(get_db)):
        result = await db.execute(
            select(model).where(model.id == item_id)
        )
        db_item = result.scalar_one_or_none()
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        for field, value in item.dict(exclude_unset=True).items():
            setattr(db_item, field, value)
        
        await db.commit()
        await db.refresh(db_item)
        return db_item
    
    @router.delete("/{item_id}")
    @protected
    async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
        result = await db.execute(
            select(model).where(model.id == item_id)
        )
        db_item = result.scalar_one_or_none()
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        await db.delete(db_item)
        await db.commit()
        return {"message": "Item deleted successfully"}

    return router
