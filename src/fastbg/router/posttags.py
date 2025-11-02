from fastbg.router.core import make_crud_router
from fastbg.db import PostTags

router = make_crud_router(PostTags)
