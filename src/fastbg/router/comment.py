from fastbg.router.core import make_crud_router
from fastbg.db import Comment

router = make_crud_router(Comment)
