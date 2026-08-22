from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.matching import router as matching_router

api_router = APIRouter()

# Include sub-routers with appropriate prefixes and tags
api_router.include_router(matching_router)
api_router.include_router(chat_router)
