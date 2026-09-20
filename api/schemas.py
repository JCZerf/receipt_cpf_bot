import dataclasses

from pydantic import BaseModel, Field

from bot.models import CpfQueryResult


class CpfLookupRequest(BaseModel):
    cpf: str = Field(min_length=11, max_length=14)
    birth_date: str = Field(min_length=8, max_length=10)


class CpfRecord(BaseModel):
    cpf: str | None = None
    name: str | None = None
    birth_date: str | None = None
    status: str | None = None
    registration_date: str | None = None
    check_digit: str | None = None
    issued_at: str | None = None
    control_code: str | None = None


class CpfLookupResponse(BaseModel):
    success: bool
    message: str
    record: CpfRecord | None = None

    @classmethod
    def from_result(cls, result: CpfQueryResult) -> "CpfLookupResponse":
        record = CpfRecord(**dataclasses.asdict(result.record)) if result.record else None
        return cls(success=result.success, message=result.message, record=record)


class HealthResponse(BaseModel):
    status: str
