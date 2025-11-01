import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from fastbg.conf import settings

DB = settings.DATABASES["default"]
URL = DB["engine"]
config = DB.get("config", {})

log = logging.getLogger("global")

engine = create_async_engine(URL, **config)

Session = async_sessionmaker(
    engine,
    class_=AsyncSession,
)

async def get_db():
    async with Session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            # sqlalchemy exception?
            await session.rollback()
            raise
        finally:
            await session.close()
