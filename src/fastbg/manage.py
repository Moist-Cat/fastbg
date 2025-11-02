import sys
import os

from fastbg.db import create_db
from fastbg.conf import settings


def get_command(command: list = sys.argv[1]):
    """Macros to maange the db"""
    if command == "shell":
        import fastbg.test.shell

    elif command == "migrate":
        import asyncio

        asyncio.run(create_db(settings.DATABASES["default"]["engine"]))

    elif command == "test":
        from fastbg.test import test_db

        test_db.run()

    elif command == "runserver":
        os.system(
            f"PYTHONPATH={settings.BASE_DIR.parent} uvicorn fastbg.server:app --port 5000 --reload"
        )


if __name__ == "__main__":
    get_command()
