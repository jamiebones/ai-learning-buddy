from fastapi import APIRouter
from app.api.endpoints import auth, chat, notes

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
