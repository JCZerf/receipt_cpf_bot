from fastapi import APIRouter, Depends, Request

from api.core.rate_limit import limiter
from api.dependencies.auth import verify_api_key
from api.models.diagnostics import DiagnosticsResponse
from bot.diagnostics import collect_diagnostics

router = APIRouter(
    prefix="/diagnostics",
    tags=["observability"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("", response_model=DiagnosticsResponse)
@limiter.limit("6/minute")
async def diagnostics(request: Request) -> DiagnosticsResponse:
    return DiagnosticsResponse(**await collect_diagnostics())
