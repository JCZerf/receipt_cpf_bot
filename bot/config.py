from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    SOLVER_URL: str
    SOLVER_API_KEY: str
    SOLVER_PATH: str = "/api/v1/recognition/hcaptcha"
    SOLVER_TIMEOUT_SECONDS: float = 30.0
    HEADLESS: bool = True


settings = BotSettings()
