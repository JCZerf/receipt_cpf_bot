from fastapi import APIRouter, Depends, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from api.core.rate_limit import limiter
from api.dependencies.auth import verify_api_key

router = APIRouter(tags=["observability"])


@router.get("/metrics", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def metrics(request: Request) -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
