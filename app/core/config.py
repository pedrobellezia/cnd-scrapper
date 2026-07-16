from os import getenv
from dotenv import load_dotenv
from pathlib import Path

# Carregar variaveis de ambiente
load_dotenv()


def get_env(name: str, *, required: bool = False) -> str | None:
    value = getenv(name)
    if required and not value:
        raise RuntimeError(f"Variável de ambiente {name} não foi encontrada.")
    return value


# Configurações de ambiente
CAPTCHA_API_KEY = get_env("CAPTCHA_API_KEY", required=True)
HEADLESS = get_env("HEADLESS", required=True).lower() == "true"
MAX_CONCURRENT_BROWSERS = int(get_env("MAX_CONCURRENT_BROWSERS", required=True))
API_KEY = get_env("API_KEY", required=True)
ALLOWED_ORIGINS = get_env("ALLOWED_ORIGINS", required=True).split(",")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

# Configurações do Playwright
PLAYWRIGHT_ARGS = [
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-infobars",
    "--disable-renderer-backgrounding",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding"
]

__all__ = [
    "CAPTCHA_API_KEY",
    "HEADLESS",
    "PLAYWRIGHT_ARGS",
    "MAX_CONCURRENT_BROWSERS",
    "API_KEY",
    "ALLOWED_ORIGINS",
    "SCREENSHOTS_DIR",
]
