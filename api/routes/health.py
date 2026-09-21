import httpx
from fastapi import APIRouter, Depends, Request

from api.core.rate_limit import limiter
from api.dependencies.auth import verify_api_key
from api.models.cpf import DeepHealthResponse, HealthResponse
from bot.config import settings
from bot.lookup.fetch import QUERY_URL

router = APIRouter(tags=["observability"])

PROBE_TIMEOUT_SECONDS = 5.0


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


async def _probe(client: httpx.AsyncClient, url: str) -> str:
    try:
        response = await client.get(url, timeout=PROBE_TIMEOUT_SECONDS, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError:
        return "down"
    return "ok"


@router.get(
    "/health/deep",
    response_model=DeepHealthResponse,
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("30/minute")
async def deep_health(request: Request) -> DeepHealthResponse:
    async with httpx.AsyncClient() as client:
        receita = await _probe(client, QUERY_URL)
        solver = await _probe(client, settings.SOLVER_URL)

    healthy = receita == "ok" and solver == "ok"
    return DeepHealthResponse(
        status="ok" if healthy else "degraded", receita=receita, solver=solver
    )
