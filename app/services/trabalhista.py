from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from app.exceptions import ScrapError, ErrorType
from app.core import logger, CAPTCHA_API_KEY
from app.utils.captcha_solver import CaptchaSolver
from pathlib import Path
import asyncio


class Trabalhista:
    @staticmethod
    async def execute_scrap(page: Page, cnpj: str):
        try:
            logger.info("Starting Trabalhista scrape for CNPJ: %s", cnpj)

            await page.goto(
                "https://cndt-certidao.tst.jus.br/inicio.faces",
                wait_until="domcontentloaded",
                timeout=30_000,
            )

            await page.locator("//*[@id='corpo']/div/div[2]/input[1]").click()
            await page.locator("//*[@id='gerarCertidaoForm:cpfCnpj']").fill(cnpj)
            await asyncio.sleep(5)

            solver = CaptchaSolver(api_key=CAPTCHA_API_KEY, page=page)

            result = await solver.solve_normal(
                img_xpath="//*[@id='idImgBase64']",
                input_xpath="//*[@id='idCampoResposta']",
            )

            if not result.get("success", False):
                raise ScrapError(
                    message=result.get("error") or "Erro ao resolver CAPTCHA",
                    cnpj=cnpj,
                    tipo_cnd="Trabalhista",
                    error_type=ErrorType.CaptchaError,
                )

            async with page.expect_download(timeout=30_000) as download_info:
                await page.locator(
                    "//*[@id='gerarCertidaoForm:btnEmitirCertidao']"
                ).click()
            download = await download_info.value

            download_path = await download.path()
            if not download_path:
                raise ScrapError(
                    message=f"Falha ao obter PDF da certidao Trabalhista para {cnpj}",
                    cnpj=cnpj,
                    tipo_cnd="Trabalhista",
                    error_type=ErrorType.DownloadError,
                )
            pdf_bytes = Path(download_path).read_bytes()

            logger.info("Trabalhista scrape completed for CNPJ: %s", cnpj)
            return pdf_bytes

        except ScrapError as e:
            e.tipo_cnd = "Trabalhista"
            e.cnpj = cnpj
            e.url = page.url
            raise
        except PlaywrightTimeout as e:
            raise ScrapError(
                message="Timeout durante Scrap da CND",
                cnpj=cnpj,
                tipo_cnd="Trabalhista",
                url=page.url,
                error_type=ErrorType.TimeoutError,
            ) from e
        except Exception as e:
            raise ScrapError(
                message=f"Erro inesperado durante Scrap da CND: {str(e)}",
                cnpj=cnpj,
                tipo_cnd="Trabalhista",
                url=page.url,
                error_type=ErrorType.ScrapError,
            ) from e
