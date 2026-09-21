import dataclasses
import time
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException

from api.core.metrics import captcha_result_total, cpf_queries_total, cpf_query_duration_seconds
from api.models.cpf import (
    CpfQueryRequest,
    CpfQueryResponse,
    ExtractedField,
    QueryMetadata,
    SourceData,
)
from bot.captcha.solver import CaptchaNotVerified, CaptchaRateLimited
from bot.lookup.fetch import QUERY_URL
from bot.models import CpfData
from bot.query import lookup_cpf

SOURCE_NAME = "Receita Federal"

# A Receita devolve 200 com a mensagem no corpo, entao o status vem do texto dela.
NOT_FOUND_MARKERS = ("nao existe", "não existe", "nao consta", "não consta")
INVALID_INPUT_MARKERS = ("data de nascimento", "cpf informado", "invalido", "inválido")


def source_error_status(message: str) -> int:
    lowered = message.lower()
    if any(marker in lowered for marker in NOT_FOUND_MARKERS):
        return 404
    if any(marker in lowered for marker in INVALID_INPUT_MARKERS):
        return 422
    return 502


def extracted_fields(record: CpfData) -> list[ExtractedField]:
    return [
        ExtractedField(
            name=data_field.name,
            origin=data_field.metadata["origin"],
            value=getattr(record, data_field.name),
        )
        for data_field in dataclasses.fields(record)
    ]


async def fetch_cpf_data(payload: CpfQueryRequest) -> CpfQueryResponse:
    started_at = time.perf_counter()
    try:
        response = await _query_and_extract(payload)
    except HTTPException:
        cpf_queries_total.labels(status="failed").inc()
        raise
    except Exception:
        cpf_queries_total.labels(status="error").inc()
        raise
    else:
        cpf_queries_total.labels(status="success").inc()
        return response
    finally:
        cpf_query_duration_seconds.observe(time.perf_counter() - started_at)


async def _query_and_extract(payload: CpfQueryRequest) -> CpfQueryResponse:
    request_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now(UTC)

    try:
        result = await lookup_cpf(payload.cpf, payload.birth_date)
    except CaptchaRateLimited as exc:
        captcha_result_total.labels(result="rate_limited").inc()
        raise HTTPException(
            status_code=503, detail={"source": SOURCE_NAME, "message": str(exc)}
        ) from None
    except CaptchaNotVerified as exc:
        captcha_result_total.labels(result="rejected").inc()
        raise HTTPException(
            status_code=502, detail={"source": SOURCE_NAME, "message": str(exc)}
        ) from None

    if result.record is None:
        captcha_result_total.labels(result="accepted").inc()
        raise HTTPException(
            status_code=source_error_status(result.message),
            detail={"source": SOURCE_NAME, "message": result.message},
        )

    captcha_result_total.labels(result="accepted").inc()

    return CpfQueryResponse(
        metadata=QueryMetadata(
            request_id=request_id,
            timestamp=timestamp,
            source_data=SourceData(
                source=SOURCE_NAME,
                source_url=QUERY_URL,
                fields=extracted_fields(result.record),
            ),
        )
    )
