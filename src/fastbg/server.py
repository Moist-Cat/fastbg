import os
import hashlib
from multiprocessing import Process

from fastapi import FastAPI

from fastbg.conf import settings
from fastbg.api import get_db
from fastbg.router import make_crud_router
from fastbg.db import User, Post

app = FastAPI(title="FastBG")


@app.get("/")
async def index():
    return {"status": "OK"}

app.include_router(make_crud_router(User))
app.include_router(make_crud_router(Post))
