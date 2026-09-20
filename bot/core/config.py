from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    PROJECT_NAME: str = "receipt_cpf_bot"
    API_V1_STR: str = "/api/v1"
    SOLVER_URL: str = "http://127.0.0.1:8001"
    SOLVER_TIMEOUT_SECONDS: float = 30.0
    SOLVER_API_KEY: str = ""
    # Headless e Xvfb produzem WebGL por software, e a Receita rejeita o token gerado.
    HEADLESS: bool = False


settings = Settings()
