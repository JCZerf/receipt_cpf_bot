from fastapi import APIRouter, Depends

from api.schemas import DiagnosticsResponse
from api.security import require_api_key
from bot.diagnostics import collect_diagnostics

router = APIRouter(
    prefix="/diagnostics",
    tags=["diagnostics"],
    dependencies=[Depends(require_api_key)],
)


@router.get("", response_model=DiagnosticsResponse)
async def diagnostics() -> DiagnosticsResponse:
    return DiagnosticsResponse(**await collect_diagnostics())
