from fastapi import APIRouter

from . import (
    users,
    auth,
)

router = APIRouter(prefix="/api")

router.include_router(users.router)
router.include_router(auth.router)
