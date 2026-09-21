from pydantic import BaseModel, Field


class DiagnosticsResponse(BaseModel):
    display: str | None = Field(default=None, examples=[":99"])
    headless: bool
    captcha_wait_seconds: float
    user_agent: str | None = None
    webgl_renderer: str | None = Field(
        default=None, examples=["ANGLE (Mesa, llvmpipe (LLVM 20.1.2 256 bits), OpenGL 4.5)"]
    )
    webdriver: bool | None = None
    device_memory: float | None = Field(default=None, examples=[8])
    hardware_concurrency: int | None = None
    languages: str | None = Field(default=None, examples=["pt-BR"])
    timezone: str | None = Field(default=None, examples=["America/Sao_Paulo"])
    screen: str | None = Field(default=None, examples=["1280x720"])
    browser_launch_seconds: float | None = None
    page_load_seconds: float | None = None
    hcaptcha_iframe: bool | None = None
    hcaptcha_iframe_seconds: float | None = None
    total_seconds: float | None = None
