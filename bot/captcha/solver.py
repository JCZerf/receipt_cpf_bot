import asyncio
import logging
import time

from patchright.async_api import Frame, Page

from bot.browser.hcaptcha import (
    click_task,
    is_valid_jpeg,
    read_image_urls,
    read_instruction,
    request_new_challenge,
    submit_challenge,
    wait_for_checkbox,
    wait_for_ready_challenge,
)
from bot.captcha.client import recognize
from bot.config import settings

logger = logging.getLogger(__name__)

MAX_ROUNDS = 20
MIN_TARGETS_TO_SUBMIT = 2

RATE_LIMIT_STATUS = 429
MAX_RATE_LIMIT_RETRIES = 6
BASE_BACKOFF_SECONDS = 5.0
MAX_BACKOFF_SECONDS = 120.0


class CaptchaNotVerified(Exception):
    pass


class CaptchaRateLimited(CaptchaNotVerified):
    pass


def backoff_delay(attempt: int) -> float:
    return min(BASE_BACKOFF_SECONDS * 2 ** (attempt - 1), MAX_BACKOFF_SECONDS)


async def _is_verified(checkbox_frame: Frame) -> bool:
    state = await checkbox_frame.locator("#checkbox").get_attribute("aria-checked")
    return state == "true"


async def _wait_for_challenge_or_verification(
    page: Page, checkbox_frame: Frame, timeout_ms: int | None = None
) -> Frame | None:
    timeout_ms = timeout_ms if timeout_ms is not None else int(settings.CAPTCHA_WAIT_SECONDS * 1000)
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if await _is_verified(checkbox_frame):
            return None
        try:
            return await wait_for_ready_challenge(page, timeout_ms=1_000)
        except TimeoutError:
            continue
    raise CaptchaNotVerified("neither a challenge nor a verification appeared")


async def auto_solver(page: Page) -> None:
    checkbox_frame = await wait_for_checkbox(page)
    await checkbox_frame.locator("#checkbox").click()

    round_num = 0
    rate_limit_hits = 0

    while round_num < MAX_ROUNDS:
        frame = await _wait_for_challenge_or_verification(page, checkbox_frame)
        if frame is None:
            logger.info("captcha verified after %d round(s)", round_num)
            return

        instruction = await read_instruction(frame)
        urls = await read_image_urls(frame)

        responses = await asyncio.gather(*(page.context.request.get(url) for url in urls))
        bodies = await asyncio.gather(*(response.body() for response in responses))

        if any(response.status == RATE_LIMIT_STATUS for response in responses):
            rate_limit_hits += 1
            if rate_limit_hits > MAX_RATE_LIMIT_RETRIES:
                raise CaptchaRateLimited(
                    f"hCaptcha image CDN still rate limiting after {MAX_RATE_LIMIT_RETRIES} retries"
                )
            delay = backoff_delay(rate_limit_hits)
            logger.warning(
                "hCaptcha image CDN returned %d, backing off %.0fs (retry %d/%d)",
                RATE_LIMIT_STATUS,
                delay,
                rate_limit_hits,
                MAX_RATE_LIMIT_RETRIES,
            )
            await asyncio.sleep(delay)
            continue

        rate_limit_hits = 0
        round_num += 1

        if not all(is_valid_jpeg(body) for body in bodies):
            logger.info("round %d served a broken image, asking for another challenge", round_num)
            await request_new_challenge(page, frame)
            continue

        selections = await recognize(instruction, bodies)
        targets = [i for i, selected in enumerate(selections, start=1) if selected]
        logger.info("round %d instruction=%r selecionadas=%s", round_num, instruction, targets)

        if len(targets) < MIN_TARGETS_TO_SUBMIT:
            logger.info(
                "round %d found only %d target(s), skipping instead of submitting",
                round_num,
                len(targets),
            )
            await submit_challenge(frame)
            await page.wait_for_timeout(1_500)
            continue

        for i in targets:
            await click_task(frame, i)
            await page.wait_for_timeout(1_000)

        await page.wait_for_timeout(3_000)
        await submit_challenge(frame)
        await page.wait_for_timeout(1_500)

    logger.warning("captcha not verified after %d rounds", MAX_ROUNDS)
    raise CaptchaNotVerified(f"hCaptcha not verified after {MAX_ROUNDS} rounds")
