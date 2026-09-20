import pytest

from bot.captcha.solver import (
    BASE_BACKOFF_SECONDS,
    MAX_BACKOFF_SECONDS,
    CaptchaNotVerified,
    CaptchaRateLimited,
    backoff_delay,
)


def test_backoff_starts_at_base():
    assert backoff_delay(1) == BASE_BACKOFF_SECONDS


def test_backoff_grows_exponentially():
    assert backoff_delay(2) == BASE_BACKOFF_SECONDS * 2
    assert backoff_delay(3) == BASE_BACKOFF_SECONDS * 4


def test_backoff_is_capped():
    assert backoff_delay(50) == MAX_BACKOFF_SECONDS


@pytest.mark.parametrize("attempt", range(1, 21))
def test_backoff_never_negative_or_unbounded(attempt):
    assert 0 < backoff_delay(attempt) <= MAX_BACKOFF_SECONDS


def test_rate_limited_is_a_not_verified_so_api_still_returns_503():
    assert issubclass(CaptchaRateLimited, CaptchaNotVerified)
