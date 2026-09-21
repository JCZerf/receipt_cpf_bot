from contextlib import asynccontextmanager

from patchright.async_api import async_playwright

from bot.browser.fingerprint import (
    LOCALE,
    SCREEN,
    TIMEZONE,
    VIEWPORT,
    browser_args,
    chrome_user_agent,
)
from bot.config import settings

PROFILE_DIR = settings.CHROME_PROFILE_DIR


def browser_binary() -> dict:
    if settings.CHROME_EXECUTABLE:
        return {"executable_path": settings.CHROME_EXECUTABLE}
    return {"channel": "chrome"}


def context_options(headless: bool) -> dict:
    options = {
        "locale": LOCALE,
        "timezone_id": TIMEZONE,
        "args": browser_args(chrome_user_agent()),
    }
    if not headless:
        return {**options, "no_viewport": True}
    return {**options, "viewport": VIEWPORT, "screen": SCREEN}


@asynccontextmanager
async def open_page(headless: bool = False):
    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=headless,
            **browser_binary(),
            **context_options(headless),
        )
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            yield page
        finally:
            await context.close()
