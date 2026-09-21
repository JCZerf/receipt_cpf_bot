import os
import re
import shutil
import subprocess
from functools import lru_cache

from bot.config import settings

CHROME_CANDIDATES = ("google-chrome", "google-chrome-stable", "chrome", "chromium")
CHROME_FALLBACK_PATH = "/opt/google/chrome/chrome"
VERSION_PATTERN = re.compile(r"(\d+)\.\d+\.\d+\.\d+")

UA_TEMPLATE = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/{major}.0.0.0 Safari/537.36"
)

SCREEN = {"width": 1920, "height": 1080}
VIEWPORT = {"width": 1912, "height": 949}

LOCALE = "pt-BR"
TIMEZONE = "America/Sao_Paulo"

# Com GPU, entrega o driver real; sem GPU (sob Xvfb), entrega Mesa/llvmpipe em vez do
# SwiftShader, que a Receita rejeita. Exige um display X: sem ele o Chrome só oferece
# SwiftShader, com ou sem estas flags.
GL_ARGS = [
    "--use-gl=angle",
    "--use-angle=gl",
    "--ignore-gpu-blocklist",
    "--disable-gpu-driver-bug-workarounds",
]


def chrome_executable() -> str | None:
    if settings.CHROME_EXECUTABLE:
        return settings.CHROME_EXECUTABLE
    for name in CHROME_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    return CHROME_FALLBACK_PATH if os.path.exists(CHROME_FALLBACK_PATH) else None


def parse_major_version(version_output: str) -> str | None:
    match = VERSION_PATTERN.search(version_output)
    return match.group(1) if match else None


def build_user_agent(major: str) -> str:
    return UA_TEMPLATE.format(major=major)


@lru_cache(maxsize=1)
def chrome_user_agent() -> str | None:
    executable = chrome_executable()
    if executable is None:
        return None
    try:
        output = subprocess.run(
            [executable, "--version"], capture_output=True, text=True, timeout=10
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    major = parse_major_version(output)
    return build_user_agent(major) if major else None


def browser_args(user_agent: str | None) -> list[str]:
    args = list(GL_ARGS)
    if user_agent:
        args.append(f"--user-agent={user_agent}")
    return args
