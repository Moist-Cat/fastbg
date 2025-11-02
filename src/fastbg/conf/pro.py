from fastbg.conf._base import *
import os

# Config
DEBUG = False
SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY)

# Database
DATABASES = {
    "default": {
        "engine": f"sqlite:///{BASE_DIR}/db.sqlite",
        "sync_engine": f"sqlite:///{TEST_DIR}/db.sqlite",
    }
}
