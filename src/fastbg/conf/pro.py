from fastbg.conf._base import *

# Config
DEBUG = False

# Database
DATABASES = {
    "default": {
        "engine": f"sqlite:///{BASE_DIR}/db.sqlite",
    }
}
