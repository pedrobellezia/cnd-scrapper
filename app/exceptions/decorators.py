from __future__ import annotations

import functools
import inspect
from pathlib import Path
import time
from playwright.async_api import TimeoutError as PlaywrightTimeout, Page
from app.core import logger
from app.exceptions.errors import ScrapError, ErrorType

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"


def handle_scrap_errors(tipo_cnd: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Obter metadados da função
            sig = inspect.signature(func)

            # Obter os parametros passados para a função
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()

            cnpj: str | None = bound_args.arguments.get("cnpj") or "Desconhecido"
            page: Page | None = bound_args.arguments.get("page")
            uf: str | None = bound_args.arguments.get("uf")
            municipio: str | None = bound_args.arguments.get("municipio")

            success = False
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except ScrapError as e:
                e.tipo_cnd = tipo_cnd
                e.cnpj = cnpj
                e.url = page.url if page else None
                raise
            except PlaywrightTimeout as e:
                raise ScrapError(
                    message="Timeout durante a execução do scraper",
                    cnpj=cnpj,
                    tipo_cnd=tipo_cnd,
                    url=page.url if page else None,
                    error_type=ErrorType.TimeoutError,
                    uf=uf if uf else None,
                    municipio=municipio if municipio else None
                ) from e
            except Exception as e:
                logger.exception(
                    "Falha interna de execução no scraper %s para CNPJ %s",
                    tipo_cnd,
                    cnpj
                )

                raise ScrapError(
                    message="Ocorreu um erro inesperado durante a execução do scraper",
                    cnpj=cnpj,
                    tipo_cnd=tipo_cnd,
                    url=page.url if page else None,
                    error_type=ErrorType.ScrapError,
                    uf=uf if uf else None,
                    municipio=municipio if municipio else None
                ) from e
            finally:
                if page and not success:
                    try:
                        filename = f"error_{int(time.time())}.png"
                        screenshot_path = SCREENSHOTS_DIR/filename

                        await page.screenshot(path=str(screenshot_path))
                        logger.info("Screenshot de erro salva em: %s", screenshot_path)
                    except Exception as e:
                        logger.error("Falha ao tirar screenshot de erro: %s", e)

        return wrapper

    return decorator
