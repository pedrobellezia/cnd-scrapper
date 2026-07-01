from playwright.async_api import (
    Page,
    BrowserContext,
    TimeoutError as PlaywrightTimeout,
    Download,
)
from app.exceptions import ScrapError, ErrorType
from app.core import logger, CAPTCHA_API_KEY
from app.utils.captcha_solver import CaptchaSolver
from pathlib import Path
from typing import Awaitable, Callable
import asyncio
import base64

from app.utils.pdf_handler import add_cnpj


class Estadual:
    @staticmethod
    async def execute_scrap(
        page: Page, context: BrowserContext, cnpj: str, uf: str
    ) -> bytes | None:
        # tipage pro pycharm parar de reclamar
        method: Callable[..., Awaitable[bytes]] | None = getattr(Estadual, uf, None)
        if not callable(method) or uf.startswith("_"):
            return None
        try:
            return await method(page=page, context=context, cnpj=cnpj)
        except ScrapError as e:
            e.tipo_cnd = f"Estadual - {uf.upper()}"
            e.cnpj = cnpj
            e.url = page.url
            raise
        except PlaywrightTimeout as e:
            raise ScrapError(
                message="Timeout durante Scrap da CND",
                cnpj=cnpj,
                tipo_cnd=f"Estadual - {uf.upper()}",
                url=page.url,
                error_type=ErrorType.TimeoutError,
            ) from e
        except Exception as e:
            raise ScrapError(
                message=f"Erro inesperado durante Scrap da CND: {str(e)}",
                cnpj=cnpj,
                tipo_cnd=f"Estadual - {uf.upper()}",
                url=page.url,
                error_type=ErrorType.ScrapError,
            ) from e

    @staticmethod
    async def sp(*, page: Page, context: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Estadual SP scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://www10.fazenda.sp.gov.br/CertidaoNegativaDeb/Pages/EmissaoCertidaoNegativa.aspx",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        await page.locator("//*[@id='MainContent_cnpjradio']").click()
        await page.locator("//*[@id='MainContent_txtDocumento']").fill(cnpj)

        solver = CaptchaSolver(api_key=CAPTCHA_API_KEY, page=page)
        result = await solver.auto_solve_v2()

        if not result.get("success", False):
            raise ScrapError(
                message=result.get("error") or "Erro ao resolver CAPTCHA",
                error_type=ErrorType.CaptchaError,
            )

        await page.locator("//*[@id='MainContent_btnPesquisar']").click()
        await asyncio.sleep(5)

        if await page.locator("//*[@class='bg-danger']").is_visible():
            raise ScrapError(
                message="Nao foi possivel obter uma certidão válida",
                error_type=ErrorType.CndUnavailable,
            )

        async with page.expect_download(timeout=30000) as dl:
            await page.locator("//*[@id='MainContent_btnImpressao']").click()
        download = await dl.value
        download_path = await download.path()
        if not download_path:
            raise ScrapError(
                message="Falha ao baixar a CND", error_type=ErrorType.DownloadError
            )
        pdf_bytes = Path(download_path).read_bytes()

        logger.info("Estadual SP scrape completed for CNPJ: %s", cnpj)
        return pdf_bytes

    @staticmethod
    async def sc(*, page: Page, context: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Estadual SC scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://sat.sef.sc.gov.br/tax.NET/Sat.CtaCte.Web/SolicitacaoCnd.aspx"
        )

        await page.locator(
            "//*[@id='Body_Main_Main_sepBusca_idnCnd_MaskedField']"
        ).fill(cnpj)

        solver = CaptchaSolver(api_key=CAPTCHA_API_KEY, page=page)
        result = await solver.auto_solve_v2()

        if not result.get("success", False):
            raise ScrapError(
                message=result.get("error"),
                error_type=ErrorType.CaptchaError,
            )

        await page.locator(
            "//a[.//span[contains(normalize-space(), 'Buscar')]]"
        ).click()

        try:
            download_task = asyncio.create_task(page.wait_for_event("download"))
            popup_task = asyncio.create_task(page.wait_for_event("popup"))

            await page.click('//*[@id="Body_Main_Main_ctnResultado_btnGerarCnd"]')

            done, _ = await asyncio.wait(
                [download_task, popup_task], return_when=asyncio.FIRST_COMPLETED
            )

            if download_task in done:
                download: Download = await download_task
                popup_task.cancel()

            else:
                popup: Page = await popup_task
                download_task.cancel()
                await popup.emulate_media(media="print")
                return await popup.pdf()

        except PlaywrightTimeout:
            link = page.locator('//ul[@class="sat-vs-success"]/li[3]/a')

            async with page.expect_download(timeout=30000) as dl:
                await link.click()

            download = await dl.value

        download_path = await download.path()
        if not download_path:
            raise ScrapError(
                message="Falha ao baixar a CND", error_type=ErrorType.DownloadError
            )
        pdf_bytes = Path(download_path).read_bytes()

        logger.info("Estadual SC scrape completed for CNPJ: %s", cnpj)

        return pdf_bytes

    @staticmethod
    async def rs(*, page: Page, context: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Estadual RS scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://www.sefaz.rs.gov.br/sat/CertidaoSitFiscalSolic.aspx",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        altcha = page.locator('//altcha-widget[@id="altcha"]')
        await altcha.wait_for(state="attached", timeout=5_000)

        challenge_url = await altcha.get_attribute("challengeurl")
        if not challenge_url:
            raise ScrapError(
                message="Erro ao obter challenge_url do ALTCHA",
                error_type=ErrorType.ScrapError,
            )

        solver = CaptchaSolver(api_key=CAPTCHA_API_KEY, page=page)

        try:
            result = await solver.solver.altcha(
                pageurl=page.url,
                challenge_url=challenge_url,
            )
            token = result["code"]
        except Exception as e:
            raise ScrapError(
                message="Erro ao resolver CAPTCHA",
                error_type=ErrorType.CaptchaError,
            ) from e

        container = page.locator(".altcha-main")
        await container.wait_for(state="attached", timeout=5_000)

        await container.evaluate(
            """(el, token) => {
                    let input = el.querySelector('input[name="altcha"]');

                    if (!input) {
                        input = document.createElement("input");
                        input.type = "hidden";
                        input.name = "altcha";
                        el.appendChild(input);
                    }

                    input.value = token;
                }""",
            token,
        )

        await page.locator("//input[@name='campoCnpj']").fill(cnpj)

        await page.evaluate(
            """
                const widget = document.querySelector('#altcha');
                if (widget) {
                    widget.dispatchEvent(new CustomEvent('statechange', {
                        detail: { state: 'verified' }
                    }));
                }
                """
        )

        async with page.expect_download(timeout=30_000) as download_info:
            await page.locator("#btnEnviar").click()

        download = await download_info.value
        download_path = await download.path()
        if not download_path:
            raise ScrapError(
                message="Falha ao baixar a CND", error_type=ErrorType.DownloadError
            )

        pdf_bytes = await add_cnpj(Path(download_path).read_bytes(), cnpj)

        logger.info("Estadual RS scrape completed for CNPJ: %s", cnpj)

        return pdf_bytes

    @staticmethod
    async def es(*, page: Page, context: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Estadual ES scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://s2-internet.sefaz.es.gov.br/certidao/cnd", timeout=90000
        )

        await page.locator(
            "//li[@title='Certidão Negativa de Débito']/a"
        ).click()

        await page.locator(
            "//input[@name='numIdentificacao']"
        ).fill(cnpj)


        sitekey = await page.locator("//div[@class='cf-turnstile']").get_attribute('data-sitekey')

        solver = CaptchaSolver(api_key=CAPTCHA_API_KEY, page=page).solver
        result = await solver.turnstile(sitekey=sitekey, url=page.url)
        code = result['code']
        await page.evaluate(f"""
                            document.querySelector('[name="cf-turnstile-response"]').value = '{code}';
                            """)


        await page.locator(
            "//button[@id='btn-emitir-certidao']"
        ).click()

        # Não está conseguindo puxar o atributo do pdf
        b64pdf = await page.locator("//div[@id='divCertidao']/object").get_attribute("data", timeout=90000)

        base64_data = b64pdf.split(",", 1)[1]

        pdf_bytes = base64.b64decode(base64_data)

        logger.info("Estadual ES scrape completed for CNPJ: %s", cnpj)

        return pdf_bytes

