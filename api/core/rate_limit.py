from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.dependencies.auth import API_KEY_HEADER


def get_rate_limit_key(request: Request) -> str:
    api_key = request.headers.get(API_KEY_HEADER)
    return api_key if api_key else get_remote_address(request)


limiter = Limiter(key_func=get_rate_limit_key)
