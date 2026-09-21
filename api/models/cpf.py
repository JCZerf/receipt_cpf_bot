from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from bot.models import normalize_birth_date, normalize_cpf


class CpfQueryRequest(BaseModel):
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
    def normalize_cpf_digits(cls, value: str) -> str:
        return normalize_cpf(value)

    @field_validator("birth_date")
    @classmethod
    def normalize_birth_date_digits(cls, value: str) -> str:
        return normalize_birth_date(value)


class ExtractedField(BaseModel):
    name: str = Field(examples=["name"])
    origin: str = Field(examples=["html"])
    value: str | None = Field(examples=["FULANO DE TAL"])


class SourceData(BaseModel):
    source: str = Field(examples=["Receita Federal"])
    source_url: str
    fields: list[ExtractedField]


class QueryMetadata(BaseModel):
    request_id: str = Field(examples=["ab12cd34"])
    timestamp: datetime
    source_data: SourceData


class CpfQueryResponse(BaseModel):
    metadata: QueryMetadata


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])


class DeepHealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    receita: str = Field(examples=["ok"])
    solver: str = Field(examples=["ok"])
