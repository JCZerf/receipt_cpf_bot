import pytest

from bot.browser.fingerprint import (
    GL_ARGS,
    LOCALE,
    SCREEN,
    TIMEZONE,
    VIEWPORT,
    browser_args,
    build_user_agent,
    parse_major_version,
)
from bot.browser.session import context_options
from bot.config import settings


def test_parse_major_version():
    assert parse_major_version("Google Chrome 140.0.7339.80 \n") == "140"


def test_parse_major_version_unknown_output():
    assert parse_major_version("command not found") is None


def test_build_user_agent_has_no_headless_marker():
    ua = build_user_agent("140")
    assert "Headless" not in ua
    assert "Chrome/140.0.0.0" in ua


def test_browser_args_select_angle_gl_over_swiftshader():
    args = browser_args(None)
    assert "--use-gl=angle" in args
    assert "--use-angle=gl" in args
    assert "--ignore-gpu-blocklist" in args
    assert not any(arg.startswith("--user-agent=") for arg in args)


def test_browser_args_include_user_agent_when_known():
    args = browser_args("UA/1.0")
    assert "--user-agent=UA/1.0" in args


def test_browser_args_do_not_mutate_shared_list():
    browser_args("UA/1.0")
    assert GL_ARGS == [
        "--use-gl=angle",
        "--use-angle=gl",
        "--ignore-gpu-blocklist",
        "--disable-gpu-driver-bug-workarounds",
    ]


def test_window_fits_inside_screen():
    assert VIEWPORT["width"] <= SCREEN["width"]
    assert VIEWPORT["height"] <= SCREEN["height"]


def test_screen_follows_settings():
    assert SCREEN == {"width": settings.SCREEN_WIDTH, "height": settings.SCREEN_HEIGHT}


def test_context_options_headful_uses_real_window():
    options = context_options(headless=False)
    assert options["no_viewport"] is True
    assert "viewport" not in options


def test_context_options_headless_sets_screen_and_viewport():
    options = context_options(headless=True)
    assert options["screen"] == SCREEN
    assert options["viewport"] == VIEWPORT


@pytest.mark.parametrize("headless", [True, False])
def test_context_options_always_brazilian(headless):
    options = context_options(headless=headless)
    assert options["locale"] == LOCALE == "pt-BR"
    assert options["timezone_id"] == TIMEZONE == "America/Sao_Paulo"


@pytest.mark.parametrize("headless", [True, False])
def test_gl_args_apply_in_both_modes(headless):
    options = context_options(headless=headless)
    assert "--use-angle=gl" in options["args"], (
        "sem estas flags o Chrome sob Xvfb cai em SwiftShader, que a Receita rejeita"
    )
    assert "--ignore-gpu-blocklist" in options["args"]
