from fastbg.router.core import make_crud_router
from fastbg.db import Post

router = make_crud_router(Post)
