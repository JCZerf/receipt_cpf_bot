from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    SOLVER_URL: str
    SOLVER_API_KEY: str
    CHROME_PROFILE_DIR: Path = Path(__file__).parent.parent / ".chrome-profile"
    CHROME_EXECUTABLE: str = ""
    SOLVER_PATH: str = "/api/v1/recognition/hcaptcha"
    SOLVER_TIMEOUT_SECONDS: float = 30.0
    HEADLESS: bool = True
    # Constantes calibradas em desktop rapido derrubam a consulta em container com pouca CPU,
    # onde o widget do hCaptcha leva bem mais tempo para renderizar.
    CAPTCHA_WAIT_SECONDS: float = 45.0


settings = BotSettings()
