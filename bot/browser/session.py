from contextlib import asynccontextmanager
from pathlib import Path

from patchright.async_api import async_playwright

PROFILE_DIR = Path(__file__).parent.parent.parent / ".chrome-profile"


@asynccontextmanager
async def open_page(headless: bool = False):
    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            PROFILE_DIR,
            channel="chrome",
            headless=headless,
            no_viewport=True,
        )
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            yield page
        finally:
            await context.close()
