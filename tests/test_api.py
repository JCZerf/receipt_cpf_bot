import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes import cpf as cpf_route
from bot.captcha.solver import CaptchaNotVerified
from bot.core.config import settings
from bot.models import CpfData, CpfQueryResult

BASE = settings.API_V1_STR


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    response = client.get(f"{BASE}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cpf_lookup_success(client, monkeypatch):
    record = CpfData(
        cpf="111.111.111-11",
        name="Fulano de Tal",
        birth_date="01/01/1990",
        status="REGULAR",
        registration_date="01/01/2000",
        check_digit="11",
    )

    async def fake_lookup(cpf, birth_date):
        assert (cpf, birth_date) == ("11111111111", "01011990")
        return CpfQueryResult(success=True, message="query completed", raw_html="", record=record)

    monkeypatch.setattr(cpf_route, "lookup_cpf", fake_lookup)

    response = client.post(f"{BASE}/cpf", json={"cpf": "11111111111", "birth_date": "01011990"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["record"]["name"] == "Fulano de Tal"
    assert body["record"]["status"] == "REGULAR"


def test_cpf_lookup_without_record(client, monkeypatch):
    async def fake_lookup(cpf, birth_date):
        return CpfQueryResult(success=False, message="CPF não encontrado", raw_html="")

    monkeypatch.setattr(cpf_route, "lookup_cpf", fake_lookup)

    response = client.post(f"{BASE}/cpf", json={"cpf": "11111111111", "birth_date": "01011990"})

    assert response.status_code == 200
    assert response.json() == {
        "success": False,
        "message": "CPF não encontrado",
        "record": None,
    }


def test_cpf_lookup_captcha_failure_returns_503(client, monkeypatch):
    async def fake_lookup(cpf, birth_date):
        raise CaptchaNotVerified("hCaptcha not verified after 20 rounds")

    monkeypatch.setattr(cpf_route, "lookup_cpf", fake_lookup)

    response = client.post(f"{BASE}/cpf", json={"cpf": "11111111111", "birth_date": "01011990"})

    assert response.status_code == 503
    assert "hCaptcha" in response.json()["detail"]


def test_cpf_lookup_rejects_short_cpf(client):
    response = client.post(f"{BASE}/cpf", json={"cpf": "123", "birth_date": "01011990"})
    assert response.status_code == 422
