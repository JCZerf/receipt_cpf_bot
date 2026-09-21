import os
import time

from bot.browser.session import open_page
from bot.config import settings
from bot.lookup.fetch import QUERY_URL

BROWSER_PROBE = """() => {
  const gl = document.createElement('canvas').getContext('webgl');
  const dbg = gl && gl.getExtension('WEBGL_debug_renderer_info');
  return {
    user_agent: navigator.userAgent,
    webgl_renderer: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : null,
    webdriver: navigator.webdriver,
    device_memory: navigator.deviceMemory ?? null,
    hardware_concurrency: navigator.hardwareConcurrency,
    languages: navigator.languages.join(','),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    screen: `${screen.width}x${screen.height}`,
  };
}"""


async def collect_diagnostics() -> dict:
    started = time.monotonic()
    result: dict = {
        "display": os.environ.get("DISPLAY"),
        "headless": settings.HEADLESS,
        "captcha_wait_seconds": settings.CAPTCHA_WAIT_SECONDS,
    }

    async with open_page(headless=settings.HEADLESS) as page:
        launched = time.monotonic()
        await page.goto("about:blank")
        result.update(await page.evaluate(BROWSER_PROBE))
        result["browser_launch_seconds"] = round(launched - started, 2)

        page_started = time.monotonic()
        await page.goto(QUERY_URL, wait_until="domcontentloaded")
        result["page_load_seconds"] = round(time.monotonic() - page_started, 2)

        widget_started = time.monotonic()
        try:
            await page.locator("iframe[src*='hcaptcha']").first.wait_for(
                state="attached", timeout=int(settings.CAPTCHA_WAIT_SECONDS * 1000)
            )
            result["hcaptcha_iframe"] = True
        except Exception:
            result["hcaptcha_iframe"] = False
        result["hcaptcha_iframe_seconds"] = round(time.monotonic() - widget_started, 2)

    result["total_seconds"] = round(time.monotonic() - started, 2)
    return result
