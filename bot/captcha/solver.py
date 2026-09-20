import asyncio
import logging

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

logger = logging.getLogger(__name__)

MAX_ROUNDS = 20
MIN_TARGETS_TO_SUBMIT = 2


class CaptchaNotVerified(Exception):
    pass


async def _is_verified(checkbox_frame: Frame) -> bool:
    state = await checkbox_frame.locator("#checkbox").get_attribute("aria-checked")
    return state == "true"


async def auto_solver(page: Page) -> None:
    checkbox_frame = await wait_for_checkbox(page)
    await checkbox_frame.locator("#checkbox").click()

    for round_num in range(1, MAX_ROUNDS + 1):
        if await _is_verified(checkbox_frame):
            logger.info("captcha verified after %d round(s)", round_num - 1)
            return

        frame = await wait_for_ready_challenge(page)
        instruction = await read_instruction(frame)
        urls = await read_image_urls(frame)

        responses = await asyncio.gather(*(page.context.request.get(url) for url in urls))
        bodies = await asyncio.gather(*(response.body() for response in responses))

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
