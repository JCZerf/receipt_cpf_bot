from fastapi import FastAPI

from bot.api.main import api_router
from bot.core.config import settings
from bot.logging_config import configure_logging

configure_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)
app.include_router(api_router, prefix=settings.API_V1_STR)
