import asyncio
import re
import time
from dataclasses import dataclass

from patchright.async_api import Frame, Page

IMAGE_URL_PATTERN = re.compile(r'url\("([^"]+)"\)')
MARGIN_TOP_PATTERN = re.compile(r"margin-top:\s*(-?[\d.]+)px")
DIMENSIONS_PATTERN = re.compile(r"width:\s*([\d.]+)px;\s*height:\s*([\d.]+)px")


def parse_image_url(style: str) -> str | None:
    match = IMAGE_URL_PATTERN.search(style)
    return match.group(1) if match else None


@dataclass
class SpriteFrame:
    url: str
    sprite_width: float
    sprite_height: float
    margin_top: float
    frame_height: float


def parse_sprite_frame(style: str, frame_height: float) -> SpriteFrame | None:
    url = parse_image_url(style)
    margin_match = MARGIN_TOP_PATTERN.search(style)
    dims_match = DIMENSIONS_PATTERN.search(style)
    if url is None or margin_match is None or dims_match is None:
        return None
    return SpriteFrame(
        url=url,
        sprite_width=float(dims_match.group(1)),
        sprite_height=float(dims_match.group(2)),
        margin_top=float(margin_match.group(1)),
        frame_height=frame_height,
    )


def frame_index(sprite: SpriteFrame) -> int:
    return round((abs(sprite.margin_top) - sprite.frame_height / 2) / sprite.frame_height)


def crop_box_for_frame(
    sprite: SpriteFrame, raw_width: int, raw_height: int
) -> tuple[int, int, int, int]:
    scale = raw_width / sprite.sprite_width
    idx = frame_index(sprite)
    top = round(idx * sprite.frame_height * scale)
    bottom = round((idx + 1) * sprite.frame_height * scale)
    return (0, top, raw_width, min(bottom, raw_height))


def is_valid_jpeg(data: bytes) -> bool:
    return data[:3] == b"\xff\xd8\xff"


def checkbox_frame(page: Page) -> Frame | None:
    return next((f for f in page.frames if "frame=checkbox" in f.url), None)


def challenge_frame(page: Page) -> Frame | None:
    return next((f for f in page.frames if "frame=challenge" in f.url), None)


async def read_instruction(frame: Frame) -> str:
    return await frame.locator("#prompt-question").inner_text()


async def _read_task_image_url(frame: Frame, i: int) -> str:
    task = frame.locator(f'.task[aria-label="Imagem do desafio {i}"]')
    style = await task.locator(".image").get_attribute("style", timeout=1_000)
    url = parse_image_url(style or "")
    if url is None:
        raise ValueError(f"could not find image url for task {i}")
    return url


async def read_image_urls(frame: Frame) -> list[str]:
    return list(await asyncio.gather(*(_read_task_image_url(frame, i) for i in range(1, 10))))


async def read_reference_sprite(frame: Frame) -> SpriteFrame | None:
    wrapper = frame.locator(".challenge-example .image-wrapper")
    if await wrapper.count() == 0:
        return None
    wrapper_style = await wrapper.get_attribute("style", timeout=1_000)
    wrapper_dims = DIMENSIONS_PATTERN.search(wrapper_style or "")
    if wrapper_dims is None:
        return None
    frame_height = float(wrapper_dims.group(2))

    image = wrapper.locator(".image")
    image_style = await image.get_attribute("style", timeout=1_000)
    return parse_sprite_frame(image_style or "", frame_height)


async def request_new_challenge(page: Page, frame: Frame) -> None:
    await frame.locator(".refresh.button").click()


async def click_task(frame: Frame, i: int) -> None:
    await frame.locator(f'.task[aria-label="Imagem do desafio {i}"]').click()


async def submit_challenge(frame: Frame) -> None:
    await frame.locator(".button-submit.button").click()


async def wait_for_checkbox(page: Page, timeout_ms: int = 15_000) -> Frame:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        frame = checkbox_frame(page)
        if frame is not None:
            try:
                await frame.locator("#checkbox").wait_for(state="attached", timeout=500)
                return frame
            except Exception:
                pass
        await asyncio.sleep(0.2)
    raise TimeoutError("checkbox frame did not become ready")


async def _reference_sprite_stable(frame: Frame) -> SpriteFrame | None:
    first = await read_reference_sprite(frame)
    await asyncio.sleep(0.3)
    second = await read_reference_sprite(frame)
    if first != second:
        raise ValueError("reference image still transitioning (stale DOM)")
    return second


async def wait_for_ready_challenge(page: Page, timeout_ms: int = 15_000) -> Frame:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        frame = challenge_frame(page)
        if frame is not None:
            try:
                await frame.locator("#prompt-question").wait_for(state="attached", timeout=500)
                urls = await read_image_urls(frame)
                if not all(urls):
                    raise ValueError("task images not ready")
                await _reference_sprite_stable(frame)
                return frame
            except Exception:
                pass
        await asyncio.sleep(0.2)
    raise TimeoutError("challenge frame did not become ready")
