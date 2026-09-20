import pytest

from bot.captcha import solver

JPEG = b"\xff\xd8\xff\xe0payload"
RATE_LIMIT_HTML = b"<!doctype html><html>rate limited</html>"


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    async def body(self):
        return self._body


class FakeLocator:
    def __init__(self, checked):
        self._checked = checked

    async def click(self):
        return None

    async def get_attribute(self, name):
        return self._checked()


class FakeFrame:
    def __init__(self, checked=lambda: "false"):
        self._checked = checked

    def locator(self, selector):
        return FakeLocator(self._checked)


class FakeRequest:
    def __init__(self, responses):
        self._responses = responses
        self.calls = 0

    async def get(self, url):
        self.calls += 1
        return self._responses()


class FakePage:
    def __init__(self, responses):
        self.context = type("Ctx", (), {"request": FakeRequest(responses)})()

    async def wait_for_timeout(self, ms):
        return None


@pytest.fixture
def wired(monkeypatch):
    state = {"new_challenge": 0, "submitted": 0, "clicked": [], "sleeps": [], "recognized": 0}

    async def fake_sleep(seconds):
        state["sleeps"].append(seconds)

    async def fake_wait_challenge(page, timeout_ms=None):
        return FakeFrame()

    async def fake_read_instruction(frame):
        return "selecione"

    async def fake_read_urls(frame):
        return [f"u{i}" for i in range(9)]

    async def fake_new_challenge(page, frame):
        state["new_challenge"] += 1

    async def fake_submit(frame):
        state["submitted"] += 1

    async def fake_click(frame, i):
        state["clicked"].append(i)

    async def fake_recognize(instruction, bodies):
        state["recognized"] += 1
        return [True, True] + [False] * 7

    monkeypatch.setattr(solver.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(solver, "wait_for_ready_challenge", fake_wait_challenge)
    monkeypatch.setattr(solver, "read_instruction", fake_read_instruction)
    monkeypatch.setattr(solver, "read_image_urls", fake_read_urls)
    monkeypatch.setattr(solver, "request_new_challenge", fake_new_challenge)
    monkeypatch.setattr(solver, "submit_challenge", fake_submit)
    monkeypatch.setattr(solver, "click_task", fake_click)
    monkeypatch.setattr(solver, "recognize", fake_recognize)
    return state


def wire_checkbox(monkeypatch, checked):
    async def fake_wait_checkbox(page):
        return FakeFrame(checked)

    monkeypatch.setattr(solver, "wait_for_checkbox", fake_wait_checkbox)


@pytest.mark.asyncio
async def test_rate_limit_backs_off_instead_of_hammering(wired, monkeypatch):
    wire_checkbox(monkeypatch, lambda: "false")
    page = FakePage(lambda: FakeResponse(429, RATE_LIMIT_HTML))

    with pytest.raises(solver.CaptchaRateLimited):
        await solver.auto_solver(page)

    assert wired["new_challenge"] == 0, "não deve pedir novo desafio enquanto está rate limited"
    assert wired["recognized"] == 0, "não deve gastar crédito do solver com página de erro"
    assert wired["sleeps"] == [5.0, 10.0, 20.0, 40.0, 80.0, 120.0]


@pytest.mark.asyncio
async def test_broken_image_without_rate_limit_requests_new_challenge(wired, monkeypatch):
    wire_checkbox(monkeypatch, lambda: "false")
    page = FakePage(lambda: FakeResponse(200, b"not-a-jpeg"))

    with pytest.raises(solver.CaptchaNotVerified):
        await solver.auto_solver(page)

    assert wired["new_challenge"] == solver.MAX_ROUNDS
    assert wired["recognized"] == 0


@pytest.mark.asyncio
async def test_verified_checkbox_returns_without_solving(wired, monkeypatch):
    wire_checkbox(monkeypatch, lambda: "true")
    page = FakePage(lambda: FakeResponse(200, JPEG))

    await solver.auto_solver(page)

    assert wired["recognized"] == 0
    assert wired["submitted"] == 0


@pytest.mark.asyncio
async def test_valid_images_are_sent_to_solver_and_submitted(wired, monkeypatch):
    checked = {"value": "false"}

    def state():
        return checked["value"]

    wire_checkbox(monkeypatch, state)
    page = FakePage(lambda: FakeResponse(200, JPEG))

    async def fake_submit(frame):
        wired["submitted"] += 1
        checked["value"] = "true"

    monkeypatch.setattr(solver, "submit_challenge", fake_submit)

    await solver.auto_solver(page)

    assert wired["recognized"] == 1
    assert wired["clicked"] == [1, 2]
    assert wired["submitted"] == 1
