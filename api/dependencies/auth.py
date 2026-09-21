import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from api.core.settings import settings

API_KEY_HEADER = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> None:
    if not secrets.compare_digest(api_key or "", settings.API_KEY):
        raise HTTPException(status_code=401, detail={"message": "API key invalida"})
