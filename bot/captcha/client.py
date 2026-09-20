import base64

import httpx

from bot.config import settings

REQUEST_TYPE = "image_label_binary"


def _data_uri(image: bytes) -> str:
    return f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"


async def recognize(
    instruction: str, images: list[bytes], reference: bytes | None = None
) -> list[bool]:
    payload = {
        "data": {
            "request_type": REQUEST_TYPE,
            "requester_question": {"en": instruction},
            "requester_question_example": [_data_uri(reference)] if reference else [],
            "tasklist": [
                {"task_key": str(i), "datapoint_uri": _data_uri(image)}
                for i, image in enumerate(images)
            ],
        }
    }
    url = f"{settings.SOLVER_URL.rstrip('/')}{settings.SOLVER_PATH}"
    headers = {"Authorization": f"Basic {settings.SOLVER_API_KEY}"}
    async with httpx.AsyncClient(timeout=settings.SOLVER_TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        grids = response.json()["data"]
    return [selected for grid in grids for selected in grid]
