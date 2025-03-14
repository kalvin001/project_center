from fastapi import APIRouter

from app.api.users import users
from app.api.auth import auth
from app.api.projects import router as projects_router
from app.api.chats import router as chats_router
from app.api.chatbots import router as chatbots_router

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects_router, prefix="/projects")
api_router.include_router(chats_router)
api_router.include_router(chatbots_router) 