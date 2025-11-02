from fastbg.router.user import router as user_router
from fastbg.router.post import router as post_router
from fastbg.router.comment import router as comment_router
from fastbg.router.tag import router as tag_router

ROUTERS = [
    user_router,
    post_router,
    comment_router,
    tag_router,
]
