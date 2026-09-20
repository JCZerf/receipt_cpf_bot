from contextlib import asynccontextmanager
from pathlib import Path

from patchright.async_api import async_playwright

from bot.browser.fingerprint import (
    LOCALE,
    SCREEN,
    TIMEZONE,
    VIEWPORT,
    browser_args,
    chrome_user_agent,
)

PROFILE_DIR = Path(__file__).parent.parent.parent / ".chrome-profile"


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
            channel="chrome",
            headless=headless,
            **context_options(headless),
        )
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            yield page
        finally:
            await context.close()
