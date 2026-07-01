from typing import Any, AsyncGenerator
from playwright.async_api import Browser, Page, BrowserContext
import asyncio
from playwright_stealth import Stealth
from .config import MAX_CONCURRENT_BROWSERS

# Estado global do Playwright
browser: Browser | None = None
semaphore = asyncio.Semaphore(MAX_CONCURRENT_BROWSERS)
stealth = Stealth()


async def get_tools() -> AsyncGenerator[tuple[Page, BrowserContext], Any]:
    """Context manager para obter page e context do Playwright com limite de concorrência."""
    if browser is None:
        raise RuntimeError(
            "Browser nao inicializado. Verifique o lifespan da aplicacao."
        )

    async with semaphore:
        context = None
        page = None
        try:
            context = await browser.new_context()
            page = await context.new_page()

            await stealth.apply_stealth_async(page)
            await stealth.apply_stealth_async(context)

            yield page, context
        finally:
            if page:
                await page.close()
            if context:
                await context.close()


def get_browser() -> Browser:
    """Retorna a instância global do browser."""
    global browser
    if browser is None:
        raise RuntimeError(
            "Browser nao inicializado. Verifique o lifespan da aplicacao."
        )
    return browser
