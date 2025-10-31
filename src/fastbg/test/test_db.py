import os
from pathlib import Path
import unittest

from fastbg.db import *
from fastbg.api import *
from fastbg.conf import settings

db = settings.DATABASES["default"]
ENGINE = db["engine"]

TEST_FILES = settings.TEST_FILES_DIR
TEST_DIR = settings.TEST_DIR

def build_test_db(
        name=ENGINE,
    ):
    """
    Create test database and schema.
    """
    engine = create_engine(name)

    # Nuke everything and build it from scratch.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    return engine

class Test_API(unittest.TestCase):
    
    def setUp(self):
        pass

def main_suite() -> unittest.TestSuite:
    s = unittest.TestSuite()
    load_from = unittest.defaultTestLoader.loadTestsFromTestCase
    s.addTests(load_from(Test_API))
    
    return s

def run():
    t = unittest.TextTestRunner()
    t.run(main_suite())
