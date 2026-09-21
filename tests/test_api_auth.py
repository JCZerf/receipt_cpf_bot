import pytest
from fastapi.testclient import TestClient

from api.core.settings import settings
from api.dependencies.auth import API_KEY_HEADER
from api.main import app
from api.services import cpf_service

BASE = settings.API_V1_STR
PAYLOAD = {"cpf": "11111111111", "birth_date": "01011990"}
PROTECTED = [
    ("post", f"{BASE}/cpf"),
    ("get", f"{BASE}/metrics"),
    ("get", f"{BASE}/health/deep"),
    ("get", f"{BASE}/diagnostics"),
]


@pytest.fixture
def client(monkeypatch):
    async def fail(cpf, birth_date):
        raise AssertionError("a consulta nao deve rodar sem autenticacao valida")

    monkeypatch.setattr(cpf_service, "lookup_cpf", fail)
    return TestClient(app)


def call(client, method, path, headers=None):
    kwargs = {"headers": headers} if headers else {}
    if method == "post":
        kwargs["json"] = PAYLOAD
    return getattr(client, method)(path, **kwargs)


@pytest.mark.parametrize("method,path", PROTECTED)
def test_protected_routes_reject_missing_key(client, method, path):
    assert call(client, method, path).status_code == 401


@pytest.mark.parametrize("method,path", PROTECTED)
def test_protected_routes_reject_wrong_key(client, method, path):
    assert call(client, method, path, {API_KEY_HEADER: "errada"}).status_code == 401


def test_rejection_uses_the_shared_error_shape(client):
    response = client.post(f"{BASE}/cpf", json=PAYLOAD)
    assert response.json() == {"detail": {"message": "API key invalida"}}


def test_auth_runs_before_payload_validation(client):
    response = client.post(f"{BASE}/cpf", json={"cpf": "x"}, headers={API_KEY_HEADER: "errada"})
    assert response.status_code == 401, "payload invalido nao deve vazar 422 a quem nao autenticou"


def test_health_stays_open_for_probes(client):
    assert client.get(f"{BASE}/health").status_code == 200
