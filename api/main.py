from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.core.exception_handlers import validation_exception_handler
from api.core.rate_limit import limiter
from api.core.settings import settings
from api.router import api_router
from core.logging_config import configure_logging

configure_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
