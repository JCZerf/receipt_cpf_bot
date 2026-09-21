from fastapi import APIRouter

from api.routes import cpf, diagnostics, health, metrics

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(metrics.router)
api_router.include_router(cpf.router)
api_router.include_router(diagnostics.router)
