import time
import logging
from pathlib import Path

from fastapi import FastAPI, Request

from fastbg.db import create_db_sync
from fastbg.router import ROUTERS
from fastbg.conf import settings

logger = logging.getLogger("global")

app = FastAPI(title="FastBG")

# hack to ensure the database is built
# even if the correct steps aren't followed
DB = settings.DATABASES["default"]
if "path" in DB:
    db_path = Path(DB["path"])
    if not db_path.exists():
        logger.info("Creating development database")
        create_db_sync(DB["sync_engine"])


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    msg = f"Process time: {process_time}"
    print(msg)
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
async def index():
    return {"status": "OK"}


for router in ROUTERS:
    app.include_router(router)
