import re
from dataclasses import dataclass, field

NON_DIGITS = re.compile(r"\D")

CPF_DIGITS = 11
BIRTH_DATE_DIGITS = 8


def only_digits(value: str) -> str:
    return NON_DIGITS.sub("", value)


def normalize_cpf(value: str) -> str:
    digits = only_digits(value)
    if len(digits) != CPF_DIGITS:
        raise ValueError(f"cpf must have {CPF_DIGITS} digits, got {len(digits)}")
    return digits


def normalize_birth_date(value: str) -> str:
    digits = only_digits(value)
    if len(digits) != BIRTH_DATE_DIGITS:
        raise ValueError(f"birth date must have {BIRTH_DATE_DIGITS} digits (ddmmyyyy)")
    return digits


@dataclass
class CpfQuery:
    cpf: str
    birth_date: str

    def __post_init__(self) -> None:
        self.cpf = normalize_cpf(self.cpf)
        self.birth_date = normalize_birth_date(self.birth_date)


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
