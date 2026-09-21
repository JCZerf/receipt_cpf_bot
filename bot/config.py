import tempfile
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    SOLVER_URL: str
    SOLVER_API_KEY: str
    # Diretorio-pai: cada consulta cria o seu proprio perfil dentro dele e o descarta no
    # fim. O Chrome permite um unico processo por perfil, entao compartilhar um diretorio
    # fixo faz a segunda consulta simultanea abortar com ProcessSingleton.
    CHROME_PROFILE_ROOT: Path = Path(tempfile.gettempdir()) / "receipt-cpf-profiles"
    CHROME_EXECUTABLE: str = ""
    SOLVER_PATH: str = "/api/v1/recognition/hcaptcha"
    SOLVER_TIMEOUT_SECONDS: float = 30.0
    HEADLESS: bool = True
    # Constantes calibradas em desktop rapido derrubam a consulta em container com pouca CPU,
    # onde o widget do hCaptcha leva bem mais tempo para renderizar.
    CAPTCHA_WAIT_SECONDS: float = 45.0
    # O llvmpipe rasteriza na CPU, entao a area da tela vira tempo de processador: a 1920x1080
    # uma consulta nao termina com meio nucleo, a 1280x720 termina.
    SCREEN_WIDTH: int = 1280
    SCREEN_HEIGHT: int = 720


settings = BotSettings()
