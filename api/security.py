import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from api.config import settings

API_KEY_HEADER = "X-API-Key"

api_key_scheme = APIKeyHeader(
    name=API_KEY_HEADER,
    scheme_name="API key",
    description="Credencial de acesso a esta API.",
    auto_error=False,
)


def require_api_key(api_key: str | None = Depends(api_key_scheme)) -> None:
    if not secrets.compare_digest(api_key or "", settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
        )
