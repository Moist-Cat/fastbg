import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt

from fastbg.conf import settings
from fastbg.query import base_query
from fastbg.db import User

DB = settings.DATABASES["default"]
URL = DB["engine"]
config = DB.get("config", {})

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")

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


ALGORITHM = "HS256"


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception as e:
        print(e)
        raise credentials_exception

    result = await db.execute(base_query(User).where(User.name == username))
    user = result.scalar_one_or_none()
    if user is None or user.is_soft_deleted:
        raise credentials_exception
    return user
