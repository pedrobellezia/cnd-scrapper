from typing import Callable, Awaitable
from selectolax.parser import HTMLParser
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
import asyncio
import random
import re
from app.utils.pdf_handler import add_cnpj


class Municipal:
    @staticmethod
    async def _execute_scrap(
        page: Page, context: BrowserContext, cnpj: str, uf: str, municipio: str
    ) -> bytes | None:
        logger.info("Starting Municipal scrape for CNPJ: %s, %s/%s", cnpj, municipio, uf)

        method_name = f"{uf}_{municipio}"
        # tipagem pro pycharm parar de reclamar
        method: Callable[..., Awaitable[bytes]] | None = getattr(
            Municipal, method_name, None
        )

        if not callable(method):
            return None

        try:
            return await method(page, context, cnpj)
        except ScrapError as e:
            e.tipo_cnd = f"Municipal - {municipio}/{uf.upper()}"
            e.cnpj = cnpj
            e.url = page.url
            raise
        except PlaywrightTimeout as e:
            raise ScrapError(
                message="Timeout durante Scrap da CND",
                cnpj=cnpj,
                tipo_cnd=f"Municipal - {municipio}/{uf.upper()}",
                url=page.url,
                error_type=ErrorType.TimeoutError,
            ) from e
        except Exception as e:
            raise ScrapError(
                message=f"Erro inesperado durante Scrap da CND: {str(e)}",
                cnpj=cnpj,
                tipo_cnd=f"Municipal - {municipio}/{uf.upper()}",
                url=page.url,
                error_type=ErrorType.ScrapError,
            ) from e

    @staticmethod
    async def __solve_betha(
        page: Page,
        _: BrowserContext,
        cnpj: str,
        municipio_id: str,
        estado_id: str,
    ) -> Download:
        await page.goto(
            "https://e-gov.betha.com.br/cdweb/",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await page.locator("//select[@id='mainForm:estados']").select_option(estado_id)
        await page.locator("//select[@id='mainForm:municipios']").select_option(
            municipio_id
        )
        await page.locator("//*[@id='mainForm:selecionar']").click()
        await page.locator("//div[contains(@class, 'cndContr')]").click()
        await page.locator("//a[contains(@class, 'cnpj')]").click()
        await asyncio.sleep(1)
        await page.locator("//*[@id='mainForm:cnpj']").fill(cnpj)
        await asyncio.sleep(1)
        await page.locator("//*[@id='mainForm:btCnpj']").click()

        t = page.locator('//strong[@class="fieldError"]')

        if await t.count() > 0:
            await asyncio.sleep(1)
            await page.locator("//*[@id='mainForm:cnpj']").fill(cnpj)
            await asyncio.sleep(1)
            await page.locator("//*[@id='mainForm:btCnpj']").click()

        await page.locator(
            "//*[@id='mainForm:t-contribuinte']/tbody/tr/td[3]/img"
        ).click()

        async with page.expect_download(timeout=30_000) as dl:
            await (
                page.frame_locator("//iframe[@class='fancybox-iframe']")
                .locator("//*[@id='download']")
                .click()
            )
        return await dl.value

    @staticmethod
    async def sc_blumenau(page: Page, _: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Municipal SC/Blumenau scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://www.blumenau.sc.gov.br/cidadao/pages/siatu/cnd/EmissaoCND.aspx",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await page.locator(
            "//*[@name='ctl00$ContentBody$cbkEmissaoCND$txtCpfCnpj']"
        ).fill(cnpj)

        solver = CaptchaSolver(api_key=CAPTCHA_API_KEY, page=page)

        result = await solver.solve_normal(
            img_xpath="//*[@id='ctl00_ContentBody_cbkEmissaoCND_ImageCaptcha']",
            input_xpath="//*[@id='ctl00_ContentBody_cbkEmissaoCND_tbCaptcha_I']",
        )

        if not result.get("success", False):
            raise ScrapError(
                message=result.get("error") or "Erro ao resolver CAPTCHA",
                cnpj=cnpj,
                tipo_cnd="Municipal - SC/Blumenau",
                error_type=ErrorType.CaptchaError,
            )

        await page.locator(
            "//*[@id='ctl00_ContentBody_cbkEmissaoCND_btPesquisar']"
        ).click()

        await asyncio.sleep(5)

        async with page.expect_download(timeout=30_000) as dl:
            await page.locator("//*[@id='ctl00_ContentBody_btnImprimir']").click()
        download = await dl.value

        download_path = await download.path()
        if not download_path:
            raise ScrapError(
                message=f"Falha ao obter PDF para {cnpj}",
                cnpj=cnpj,
                tipo_cnd="Municipal - SC/Blumenau",
                error_type=ErrorType.DownloadError,
            )
        pdf_bytes = Path(download_path).read_bytes()

        logger.info("Municipal SC/Blumenau scrape completed for CNPJ: %s", cnpj)
        return pdf_bytes

    @classmethod
    async def sc_florianopolis(
        cls, page: Page, context: BrowserContext, cnpj: str
    ) -> bytes:
        download_info = await cls.__solve_betha(
            page, context, cnpj, municipio_id="94", estado_id="22"
        )

        download_path = await download_info.path()
        if not download_path:
            raise ScrapError(
                message=f"Falha ao obter PDF para {cnpj}",
                cnpj=cnpj,
                tipo_cnd="Municipal - SC/Florianopolis",
                error_type=ErrorType.DownloadError,
            )
        pdf_bytes = Path(download_path).read_bytes()

        logger.info("Municipal SC/Florianopolis scrape completed for CNPJ: %s", cnpj)
        return pdf_bytes

    @classmethod
    async def mg_para_de_minas(
            cls, page: Page, context: BrowserContext, cnpj: str
    ) -> bytes:
        download_info = await cls.__solve_betha(
            page, context, cnpj, municipio_id="7267", estado_id="17"
        )

        download_path = await download_info.path()
        if not download_path:
            raise ScrapError(
                message=f"Falha ao obter PDF para {cnpj}",
                cnpj=cnpj,
                tipo_cnd="Municipal - SC/Florianopolis",
                error_type=ErrorType.DownloadError,
            )
        pdf_bytes = Path(download_path).read_bytes()

        logger.info("Municipal SC/Florianopolis scrape completed for CNPJ: %s", cnpj)
        return pdf_bytes

    @classmethod
    async def sc_lages(cls, page: Page, context: BrowserContext, cnpj: str) -> bytes:
        download_info = await cls.__solve_betha(
            page, context, cnpj, municipio_id="35", estado_id="22"
        )

        download_path = await download_info.path()
        if not download_path:
            raise ScrapError(
                message=f"Falha ao obter PDF para {cnpj}",
                cnpj=cnpj,
                tipo_cnd="Municipal - SC/Lages",
                error_type=ErrorType.DownloadError,
            )
        pdf_bytes = Path(download_path).read_bytes()

        logger.info("Municipal SC/Lages scrape completed for CNPJ: %s", cnpj)
        return pdf_bytes

    @classmethod
    async def sc_braco_do_norte(
        cls, page: Page, context: BrowserContext, cnpj: str
    ) -> bytes:
        download_info = await cls.__solve_betha(
            page, context, cnpj, municipio_id="91", estado_id="22"
        )

        download_path = await download_info.path()
        if not download_path:
            raise ScrapError(
                message=f"Falha ao obter PDF para {cnpj}",
                cnpj=cnpj,
                tipo_cnd="Municipal - SC/Braco do Norte",
                error_type=ErrorType.DownloadError,
            )
        pdf_bytes = Path(download_path).read_bytes()

        logger.info("Municipal SC/Braco do Norte scrape completed for CNPJ: %s", cnpj)
        return pdf_bytes

    @classmethod
    async def sc_criciuma(cls, page: Page, context: BrowserContext, cnpj: str) -> bytes:
        download_info = await cls.__solve_betha(
            page, context, cnpj, municipio_id="29", estado_id="22"
        )

        download_path = await download_info.path()
        if not download_path:
            raise ScrapError(
                message=f"Falha ao obter PDF para {cnpj}",
                cnpj=cnpj,
                tipo_cnd="Municipal - SC/Criciuma",
                error_type=ErrorType.DownloadError,
            )
        pdf_bytes = Path(download_path).read_bytes()

        logger.info("Municipal SC/Criciuma scrape completed for CNPJ: %s", cnpj)
        return pdf_bytes

    @staticmethod
    async def sc_itapema(page: Page, _: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Municipal SC/Itapema scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://itapema-sc.prefeituramoderna.com.br/meuiptu/index.php",
            wait_until="domcontentloaded",
            timeout=30_000,
        )

        await asyncio.sleep(0.5)
        await page.locator("//a[@id='cnd']").click()
        await page.locator("//input[@name='nrcpfcnpj']").fill(cnpj)
        await page.locator("//input[@name='nmrequerente']").fill("segredo")  # dado fictício, mas o campo é obrigatório
        await page.locator("//input[@name='nrdocumento']").fill("52998224725")  # dado fictício, mas o campo é obrigatório

        async with page.expect_popup() as popup_info:
            await page.locator("//input[@value='Emitir a Certidão']").click()
        popup = await popup_info.value

        await popup.emulate_media(media="print")
        pdf_bytes = await popup.pdf(format="A4")

        logger.info("Municipal SC/Itapema scrape completed for CNPJ: %s", cnpj)

        return pdf_bytes

    @staticmethod
    async def sc_balneario_camboriu(page: Page, _: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Municipal SC/Camboriu scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://cidadao.bc.sc.gov.br/cidadao/balneario_camboriu/portal/servicos/certidoes/emissao?params=MTU%3D",
            wait_until="domcontentloaded",
            timeout=30_000,
        )

        await page.locator("//select[@formcontrolname='idFinalidade']").select_option(
            value="1: 5"
        )

        await page.locator("//input[@formcontrolname='cpfCnpj']").fill(cnpj)

        await page.locator("//cidadao-button[@type='submit']").click()

        async with page.expect_download(timeout=30_000) as dl:
            await page.locator("//cidadao-button[@icon='fa fa-download']").click()
        download = await dl.value

        download_path = await download.path()
        if not download_path:
            raise ScrapError(
                message=f"Falha ao obter PDF para {cnpj}",
                error_type=ErrorType.DownloadError,
            )
        pdf_bytes = Path(download_path).read_bytes()

        logger.info("Municipal SC/Camboriu scrape completed for CNPJ: %s", cnpj)

        return pdf_bytes

    @staticmethod
    async def sc_joinville(page: Page, _: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Municipal SC/Joinville scrape for CNPJ: %s", cnpj)

        await page.goto("https://tmiweb.joinville.sc.gov.br/sefaz/jsp/cnd/index.jsp")

        await page.locator("//select[@id='finalidade']").select_option(value="6")

        await page.locator("//input[@name='cnpj']").fill(cnpj)

        await page.locator("//input[@value='Pesquisar']").click()

        await page.locator("//select[@id='ctp_codigo']").select_option(value="8")

        old_url = page.url

        await page.locator("//input[contains(@value, 'Gerar cert')]").click()

        await page.wait_for_url(lambda current_url: current_url != old_url)

        url = page.url

        response = await page.context.request.get(url)
        if not response.ok:
            raise ScrapError(
                message="Falha ao baixar a CND", error_type=ErrorType.DownloadError
            )

        pdf_bytes = await response.body()

        logger.info("Municipal SC/Joinville scrape completed for CNPJ: %s", cnpj)

        return pdf_bytes

    @staticmethod
    async def sp_sao_paulo(page: Page, _: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Municipal SP/Sao Paulo scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://duc.prefeitura.sp.gov.br/certidoes/forms_anonimo/frmConsultaEmissaoCertificado.aspx"
        )
        await asyncio.sleep(random.uniform(1, 2))

        await page.locator(
            '//*[@id="ctl00_ConteudoPrincipal_ddlTipoCertidao"]'
        ).select_option(value="1")

        await asyncio.sleep(random.uniform(1, 2))

        await page.locator('//*[@id="ctl00_ConteudoPrincipal_txtCNPJ"]').fill(cnpj)

        await asyncio.sleep(random.uniform(1, 2))
        imgpath = '//*[@id="ctl00_ConteudoPrincipal_imgCaptcha"]'
        input_path = '//*[@id="ctl00_ConteudoPrincipal_txtValorCaptcha"]'

        solver = CaptchaSolver(api_key=CAPTCHA_API_KEY, page=page)

        result_1 = await solver.solve_normal(
            img_xpath=imgpath,
            input_xpath=input_path,
        )

        if not result_1.get("success", False):
            raise ScrapError(
                message=result_1.get("error") or "Erro ao resolver CAPTCHA",
                error_type=ErrorType.CaptchaError,
            )

        await asyncio.sleep(random.uniform(1, 2))

        await page.click('//*[@id="ctl00_ConteudoPrincipal_btnEmitir"]')

        result_2 = await solver.solve_normal(
            img_xpath="xpath=/html/body/img[1]",
            input_xpath='//*[@id="ans"]',
        )

        if not result_2.get("success", False):
            raise ScrapError(
                message=result_2.get("error") or "Erro ao resolver CAPTCHA",
                error_type=ErrorType.CaptchaError,
            )

        async with page.expect_download(timeout=30_000) as dl:
            await page.click('//*[@id="jar"]')

        download = await dl.value

        download_path = await download.path()
        if not download_path:
            raise ScrapError(
                message=f"Falha ao obter PDF para {cnpj}",
                error_type=ErrorType.DownloadError,
            )
        pdf_bytes = await add_cnpj(Path(download_path).read_bytes(), cnpj)

        logger.info("Municipal SP/Sao Paulo scrape completed for CNPJ: %s", cnpj)

        return pdf_bytes

    @staticmethod
    async def sc_icara(page: Page, _: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Municipal SC/Icara scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://icara-sc.prefeituramoderna.com.br/meuiptu/index.php",
            wait_until="domcontentloaded",
            timeout=30_000,
        )

        await asyncio.sleep(1)
        await page.locator("//a[@id='cnd']").click()
        await page.locator("//input[@name='nrcpfcnpj']").fill(cnpj)
        await page.locator("//input[@name='nmrequerente']").fill("segredo")  # dado fictício, mas o campo é obrigatório
        await page.locator("//input[@name='nrdocumento']").fill("52998224725")  # dado fictício, mas o campo é obrigatório

        async with page.expect_popup() as popup_info:
            await page.locator("//input[@value='Emitir a Certidão']").click()
        popup = await popup_info.value

        await popup.emulate_media(media="print")
        pdf_bytes = await popup.pdf(format="A4")

        logger.info("Municipal SC/Icara scrape completed for CNPJ: %s", cnpj)

        return pdf_bytes

    @staticmethod
    async def es_vitoria(page: Page, _: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Municipal ES/Vitoria scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://tributario.vitoria.es.gov.br/Servicos/CertidaoNegativa/CertidaoNegativa.aspx",
            wait_until="domcontentloaded",
            timeout=15000
        )

        await page.locator('//input[@value="CNPJ"]').click()

        await page.locator("//input[@maxlength='14']").fill(cnpj)

        await page.locator("//input[@value='Continuar']").click()

        try:
            await page.locator("//span[@id='ctl00_conteudo_lblMensagemExcluir']").wait_for(timeout=3000)
            raise ScrapError(
                message="Não foi possível emitir a CND",
                cnpj=cnpj,
                tipo_cnd="Municipal - ES/Vitoria",
                error_type=ErrorType.ScrapError,
            )
        except PlaywrightTimeout:
            pass

        texto = await page.locator("//input[@value='Emitir']").get_attribute("onclick")

        foo = re.search(r"'([^']*)'", texto).group(1)

        nova_url = page.url.rsplit("/", 1)[0] + f"/{foo}"
        response = await page.context.request.get(nova_url)

        if not response.ok:
            raise ScrapError(
                message=f"Erro ao baixar CND: {response.status}",
                cnpj=cnpj,
                tipo_cnd="Municipal - ES/Vitoria",
                error_type=ErrorType.DownloadError,
            )

        pdf_bytes = await response.body()

        logger.info("Municipal ES/Vitoria scrape completed for CNPJ: %s", cnpj)

        return pdf_bytes

    @staticmethod
    async def rs_nova_prata(page: Page, _: BrowserContext, cnpj: str) -> bytes:
        logger.info("Starting Municipal RS/Nova Prata scrape for CNPJ: %s", cnpj)

        await page.goto(
            "https://novaprata.multi24h.com.br/multi24/sistemas/portal/",
            wait_until="domcontentloaded",
            timeout=15000
        )

        consult_url = "https://novaprata.multi24h.com.br/multi24/sistemas/portal/multi24/portal/tributacao/emitir_certidoes_login/consultar"
        consult_form_data = {
            "emitir_certidoes[cpf]": "",
            "emitir_certidoes[dtnasc]": "",
            "emitir_certidoes[cnpj]": cnpj,
            "emitir_certidoes[cadastro]": "",
            "emitir_certidoes[numero_matricula]": "",
            "emitir_certidoes[tipo_busca]": "cnpj"
        }

        search_response = await page.request.post(url=consult_url, form=consult_form_data)
        parser = HTMLParser(await search_response.text())
        row = parser.css_first("table#tbl_relacao_cadastros > tbody > tr:nth-of-type(2)")

        if not row:
            raise ScrapError(
                message="Não foi possível emitir a CND",
                cnpj=cnpj,
                tipo_cnd="Municipal - RS/Nova Prata",
                error_type=ErrorType.ScrapError,
            )

        data_id = row.attributes.get("data-id")

        generate_cnd_url = "https://novaprata.multi24h.com.br/multi24/sistemas/portal/multi24/portal/tributacao/emitir_certidoes_login/gerar_negativa"
        generate_form_data = {
            "id": data_id,
            "tipo": "1"
        }

        cnd_generation_response = await page.request.post(url=generate_cnd_url, form=generate_form_data)
        cnd_data = await cnd_generation_response.json()
        pdf_relative_path = cnd_data.get("filepath")

        if not pdf_relative_path:
            raise ScrapError(
                message="Não foi possível emitir a CND",
                cnpj=cnpj,
                tipo_cnd="Municipal - RS/Nova Prata",
                error_type=ErrorType.DownloadError,
            )


        pdf_response = await page.request.get(url=page.url + pdf_relative_path)
        pdf_bytes = await pdf_response.body()

        logger.info("Municipal RS/Nova Prata scrape completed for CNPJ: %s", cnpj)

        return pdf_bytes
