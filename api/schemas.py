import dataclasses

from pydantic import BaseModel, ConfigDict, Field, field_validator

from bot.models import CpfQueryResult, normalize_birth_date, normalize_cpf


class CpfLookupRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"cpf": "12345678901", "birth_date": "01011990"}],
        }
    )

    cpf: str = Field(
        min_length=11,
        max_length=14,
        description="CPF com 11 digitos. Aceita pontuacao: 123.456.789-01.",
        examples=["12345678901", "123.456.789-01"],
    )
    birth_date: str = Field(
        min_length=8,
        max_length=10,
        description="Data de nascimento. Aceita separadores: 01/01/1990 ou 01-01-1990.",
        examples=["01011990", "01/01/1990"],
    )

    @field_validator("cpf")
    @classmethod
    def _clean_cpf(cls, value: str) -> str:
        return normalize_cpf(value)

    @field_validator("birth_date")
    @classmethod
    def _clean_birth_date(cls, value: str) -> str:
        return normalize_birth_date(value)


class CpfRecord(BaseModel):
    cpf: str | None = Field(default=None, examples=["123.456.789-01"])
    name: str | None = Field(default=None, examples=["FULANO DE TAL"])
    birth_date: str | None = Field(default=None, examples=["01/01/1990"])
    status: str | None = Field(default=None, examples=["REGULAR"])
    registration_date: str | None = Field(default=None, examples=["13/11/1996"])
    check_digit: str | None = Field(default=None, examples=["00"])
    issued_at: str | None = Field(
        default=None,
        examples=["21:25:32 do dia 20/09/2026 (hora e data de Brasilia)."],
    )
    control_code: str | None = Field(default=None, examples=["657E.506A.7EC0.2346"])


class CpfLookupResponse(BaseModel):
    success: bool = Field(examples=[True])
    message: str = Field(examples=["query completed"])
    record: CpfRecord | None = None

    @classmethod
    def from_result(cls, result: CpfQueryResult) -> "CpfLookupResponse":
        record = CpfRecord(**dataclasses.asdict(result.record)) if result.record else None
        return cls(success=result.success, message=result.message, record=record)


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])


class DiagnosticsResponse(BaseModel):
    display: str | None = Field(default=None, examples=[":99"])
    headless: bool
    captcha_wait_seconds: float
    user_agent: str | None = None
    webgl_renderer: str | None = Field(
        default=None, examples=["ANGLE (Mesa, llvmpipe (LLVM 20.1.2 256 bits), OpenGL 4.5)"]
    )
    webdriver: bool | None = None
    device_memory: float | None = Field(default=None, examples=[8])
    hardware_concurrency: int | None = None
    languages: str | None = Field(default=None, examples=["pt-BR"])
    timezone: str | None = Field(default=None, examples=["America/Sao_Paulo"])
    screen: str | None = Field(default=None, examples=["1920x1080"])
    browser_launch_seconds: float | None = None
    page_load_seconds: float | None = None
    hcaptcha_iframe: bool | None = None
    hcaptcha_iframe_seconds: float | None = None
    total_seconds: float | None = None
