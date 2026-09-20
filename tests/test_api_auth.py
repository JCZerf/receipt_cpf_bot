import pytest
from fastapi.testclient import TestClient

from api.config import settings
from api.main import app
from api.routes import cpf as cpf_route
from api.security import API_KEY_HEADER
from bot.models import CpfQueryResult

BASE = settings.API_V1_STR
PAYLOAD = {"cpf": "11111111111", "birth_date": "01011990"}


@pytest.fixture
def client(monkeypatch):
    async def fake_lookup(cpf, birth_date):
        raise AssertionError("a consulta nao deve ser executada sem autenticacao valida")

    monkeypatch.setattr(cpf_route, "lookup_cpf", fake_lookup)
    return TestClient(app)


def test_lookup_without_key_is_rejected(client):
    response = client.post(f"{BASE}/cpf", json=PAYLOAD)
    assert response.status_code == 401


def test_lookup_with_wrong_key_is_rejected(client):
    response = client.post(f"{BASE}/cpf", json=PAYLOAD, headers={API_KEY_HEADER: "errada"})
    assert response.status_code == 401


def test_lookup_with_empty_key_is_rejected(client):
    response = client.post(f"{BASE}/cpf", json=PAYLOAD, headers={API_KEY_HEADER: ""})
    assert response.status_code == 401


def test_auth_runs_before_payload_validation(client):
    response = client.post(f"{BASE}/cpf", json={"cpf": "x"}, headers={API_KEY_HEADER: "errada"})
    assert response.status_code == 401, (
        "payload invalido nao deve revelar 422 a quem nao autenticou"
    )


def test_health_stays_open_for_probes(client):
    assert client.get(f"{BASE}/health").status_code == 200


def test_lookup_with_correct_key_passes_auth(client, monkeypatch):
    async def fake_lookup(cpf, birth_date):
        return CpfQueryResult(success=False, message="ok", raw_html="")

    monkeypatch.setattr(cpf_route, "lookup_cpf", fake_lookup)

    response = client.post(f"{BASE}/cpf", json=PAYLOAD, headers={API_KEY_HEADER: settings.API_KEY})

    assert response.status_code == 200
