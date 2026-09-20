from dataclasses import dataclass, field


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
