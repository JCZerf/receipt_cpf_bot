import secrets

from fastapi import Header, HTTPException, status

from api.config import settings

API_KEY_HEADER = "X-API-Key"


def require_api_key(api_key: str = Header(default="", alias=API_KEY_HEADER)) -> None:
    if not secrets.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
            headers={"WWW-Authenticate": API_KEY_HEADER},
        )
