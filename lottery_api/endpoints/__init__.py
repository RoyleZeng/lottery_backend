from fastapi import FastAPI

# Import all router modules
from .auth import router as auth_router
from .lottery import router as lottery_router
from .email import router as email_router


def register_routers(app: FastAPI):
    """Register all API routers with the FastAPI app"""
    app.include_router(auth_router)
    app.include_router(lottery_router)
    app.include_router(email_router)
