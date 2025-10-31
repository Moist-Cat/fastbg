from code import InteractiveConsole

# to avoid ^[[A nonsense when pressing up arrow
import readline
from fastbg.conf import settings
from fastbg.db import *
from fastbg.api import *

URL = settings.DATABASES["default"]["engine"]

banner = """
#######################################
# fastbg database interactive console #
#######################################
A Client instance is already defined (as 'client') and connected to the database.
Use it to make queries.
"""
i = InteractiveConsole(locals=locals())
i.interact(banner=banner)
