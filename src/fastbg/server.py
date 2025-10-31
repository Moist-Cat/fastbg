import os
import hashlib
from multiprocessing import Process

from fastapi import FastAPI

from fastbg.conf import settings
from fastbg.api import get_db

app = FastAPI(title="FastBG")


@app.get("/")
async def index():
    db = await get_db()
    print(db)
    return {"status": "OK"}
