from fastapi import APIRouter

from . import api_keys

# Must be used because of the way FastAPI works with nested routes

router = APIRouter(prefix = "/users")

router.include_router(api_keys.router, tags=["Users: Keys"])
