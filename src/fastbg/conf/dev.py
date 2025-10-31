from fastbg.conf._base import *

# Paths
TEST_DIR = Path(__file__).parent.parent / "test"

# Config
DEBUG = True
# Database
DATABASES = {
    "test": {
        "engine": f"sqlite+aiosqlite:///{TEST_DIR}/test_db.sqlite",
    },
    "default": {
        "engine": f"sqlite+aiosqlite:///{TEST_DIR}/dev_db.sqlite",
    },
}
