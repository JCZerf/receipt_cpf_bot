from dataclasses import fields as dataclass_fields

from bs4 import BeautifulSoup

from bot.models import CpfData, CpfQueryResult

REQUIRED_FIELDS = {"cpf", "name", "birth_date", "status", "registration_date", "check_digit"}


def _label_and_value(span) -> tuple[str, str]:
    text = span.get_text(" ", strip=True)
    label, _, value = text.partition(":")
    return label.strip().lower(), value.strip()


def extract_result(html: str) -> CpfQueryResult:
    soup = BeautifulSoup(html, "html.parser")
    spans = soup.select("span.clConteudoDados, span.clConteudoComp")
    labeled_spans = [_label_and_value(span) for span in spans]

    values: dict[str, str] = {}
    for record_field in dataclass_fields(CpfData):
        keyword = record_field.metadata["path"].rstrip(":").lower()
        for label, value in labeled_spans:
            if keyword in label:
                values[record_field.name] = value
                break

    if REQUIRED_FIELDS.issubset(values):
        record = CpfData(**values)
        return CpfQueryResult(success=True, message="query completed", raw_html=html, record=record)

    error_box = soup.select_one("#idMensagemErro")
    if error_box and error_box.get_text(strip=True):
        return CpfQueryResult(success=False, message=error_box.get_text(strip=True), raw_html=html)

    return CpfQueryResult(success=False, message="unrecognized response", raw_html=html)
