from fastapi import APIRouter

from bot.api.routes import cpf, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(cpf.router)
