from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    PROJECT_NAME: str = "receipt_cpf_bot"
    API_V1_STR: str = "/api/v1"
    API_KEY: str


settings = ApiSettings()
