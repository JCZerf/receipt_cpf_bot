from fastapi import APIRouter, Depends, Request

from api.core.rate_limit import limiter
from api.dependencies.auth import verify_api_key
from api.models.cpf import CpfQueryRequest, CpfQueryResponse
from api.services.cpf_service import fetch_cpf_data

router = APIRouter(prefix="/cpf", tags=["cpf"], dependencies=[Depends(verify_api_key)])


@router.post("", response_model=CpfQueryResponse)
@limiter.limit("30/minute")
async def query_cpf(request: Request, payload: CpfQueryRequest) -> CpfQueryResponse:
    return await fetch_cpf_data(payload)
