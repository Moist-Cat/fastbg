import logging

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from fastbg.conf import settings

DB = settings.DATABASES["default"]
URL = DB["engine"]
config = DB.get("config", {})

log = logging.getLogger("global")

engine = create_async_engine(URL, **config)
SessionLocal = sessionmaker(engine, class_=AsyncSession)

async def get_db():
    session = SessionLocal()
    return session
