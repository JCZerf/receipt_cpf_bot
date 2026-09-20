from fastapi import APIRouter, HTTPException

from api.schemas import CpfLookupRequest, CpfLookupResponse
from bot.captcha.solver import CaptchaNotVerified
from bot.query import lookup_cpf

router = APIRouter(prefix="/cpf", tags=["cpf"])


@router.post("", response_model=CpfLookupResponse)
async def query_cpf(request: CpfLookupRequest) -> CpfLookupResponse:
    try:
        result = await lookup_cpf(request.cpf, request.birth_date)
    except CaptchaNotVerified as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    return CpfLookupResponse.from_result(result)
