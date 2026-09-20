import dataclasses
from dataclasses import dataclass, field

from pydantic import BaseModel, Field


@dataclass
class CpfQuery:
    cpf: str
    birth_date: str


@dataclass
class CpfData:
    cpf: str | None = field(
        default=None,
        metadata={"origin": "html", "path": "CPF:"},
    )
    name: str | None = field(
        default=None,
        metadata={"origin": "html", "path": "Nome:"},
    )
    birth_date: str | None = field(
        default=None,
        metadata={"origin": "html", "path": "Data de Nascimento:"},
    )
    status: str | None = field(
        default=None,
        metadata={"origin": "html", "path": "Situação Cadastral:"},
    )
    registration_date: str | None = field(
        default=None,
        metadata={"origin": "html", "path": "Data da Inscrição:"},
    )
    check_digit: str | None = field(
        default=None,
        metadata={"origin": "html", "path": "Digito Verificador:"},
    )
    issued_at: str | None = field(
        default=None,
        metadata={"origin": "html", "path": "Comprovante emitido às:"},
    )
    control_code: str | None = field(
        default=None,
        metadata={"origin": "html", "path": "Código de controle do comprovante:"},
    )


@dataclass
class CpfQueryResult:
    success: bool
    message: str
    raw_html: str
    record: CpfData | None = None


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
