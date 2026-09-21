import pytest
from fastapi.testclient import TestClient

from api.core.settings import settings
from api.dependencies.auth import API_KEY_HEADER
from api.main import app
from api.services import cpf_service
from bot.captcha.solver import CaptchaNotVerified, CaptchaRateLimited
from bot.models import CpfData, CpfQueryResult

BASE = settings.API_V1_STR
PAYLOAD = {"cpf": "11111111111", "birth_date": "01011990"}

RECORD = CpfData(
    cpf="111.111.111-11",
    name="Fulano de Tal",
    birth_date="01/01/1990",
    status="REGULAR",
    registration_date="01/01/2000",
    check_digit="11",
)


@pytest.fixture
def client():
    return TestClient(app, headers={API_KEY_HEADER: settings.API_KEY})


def patch_lookup(monkeypatch, result=None, error=None, spy=None):
    async def fake_lookup(cpf, birth_date):
        if spy is not None:
            spy.update(cpf=cpf, birth_date=birth_date)
        if error is not None:
            raise error
        return result

    monkeypatch.setattr(cpf_service, "lookup_cpf", fake_lookup)


def test_health(client):
    response = client.get(f"{BASE}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_successful_query_returns_metadata_envelope(client, monkeypatch):
    patch_lookup(
        monkeypatch,
        result=CpfQueryResult(success=True, message="ok", raw_html="", record=RECORD),
    )

    body = client.post(f"{BASE}/cpf", json=PAYLOAD).json()

    metadata = body["metadata"]
    assert len(metadata["request_id"]) == 8
    assert metadata["timestamp"]
    assert metadata["source_data"]["source"] == "Receita Federal"
    assert metadata["source_data"]["source_url"].startswith("https://")


def test_fields_carry_name_origin_and_value(client, monkeypatch):
    patch_lookup(
        monkeypatch,
        result=CpfQueryResult(success=True, message="ok", raw_html="", record=RECORD),
    )

    fields = client.post(f"{BASE}/cpf", json=PAYLOAD).json()["metadata"]["source_data"]["fields"]
    by_name = {field["name"]: field for field in fields}

    assert by_name["name"] == {"name": "name", "origin": "html", "value": "Fulano de Tal"}
    assert by_name["status"]["value"] == "REGULAR"
    assert by_name["issued_at"]["value"] is None


def test_masked_input_reaches_the_bot_as_digits(client, monkeypatch):
    spy: dict[str, str] = {}
    patch_lookup(
        monkeypatch,
        result=CpfQueryResult(success=True, message="ok", raw_html="", record=RECORD),
        spy=spy,
    )

    client.post(f"{BASE}/cpf", json={"cpf": "123.456.789-01", "birth_date": "01/01/1990"})

    assert spy == {"cpf": "12345678901", "birth_date": "01011990"}


def test_cpf_not_found_is_404(client, monkeypatch):
    patch_lookup(
        monkeypatch,
        result=CpfQueryResult(success=False, message="CPF nao consta na base", raw_html=""),
    )

    response = client.post(f"{BASE}/cpf", json=PAYLOAD)

    assert response.status_code == 404
    assert response.json()["detail"]["source"] == "Receita Federal"


def test_wrong_birth_date_is_422(client, monkeypatch):
    patch_lookup(
        monkeypatch,
        result=CpfQueryResult(success=False, message="Data de nascimento invalida", raw_html=""),
    )

    assert client.post(f"{BASE}/cpf", json=PAYLOAD).status_code == 422


def test_unrecognized_source_response_is_502(client, monkeypatch):
    patch_lookup(
        monkeypatch,
        result=CpfQueryResult(success=False, message="unrecognized response", raw_html=""),
    )

    assert client.post(f"{BASE}/cpf", json=PAYLOAD).status_code == 502


def test_captcha_not_verified_is_502(client, monkeypatch):
    patch_lookup(monkeypatch, error=CaptchaNotVerified("hCaptcha not verified"))

    assert client.post(f"{BASE}/cpf", json=PAYLOAD).status_code == 502


def test_captcha_rate_limited_is_503(client, monkeypatch):
    patch_lookup(monkeypatch, error=CaptchaRateLimited("still rate limiting"))

    assert client.post(f"{BASE}/cpf", json=PAYLOAD).status_code == 503


def test_invalid_payload_uses_the_shared_error_shape(client):
    response = client.post(f"{BASE}/cpf", json={"cpf": "123", "birth_date": "01011990"})

    assert response.status_code == 422
    assert response.json() == {"detail": {"message": "Dados invalidos"}}
