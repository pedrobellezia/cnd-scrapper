from __future__ import annotations

from playwright.async_api import async_playwright, Playwright
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import SCREENSHOTS_DIR
from starlette.staticfiles import StaticFiles
import app.core.dependencies as deps
from app.core import (
    HEADLESS,
    PLAYWRIGHT_ARGS,
    setup_logging,
    add_routes,
    add_middlewares,
    add_exceptions,
)

setup_logging()


@asynccontextmanager
async def lifespan(_):
    """Gerencia ciclo de vida da aplicação: inicializa e fecha o browser."""
    playwright: Playwright | None = None

    try:
        playwright = await async_playwright().start()
        deps.browser = await playwright.chromium.launch(
            args=PLAYWRIGHT_ARGS,
            headless=HEADLESS,
        )
        yield
    finally:
        if deps.browser:
            await deps.browser.close()
        if playwright:
            await playwright.stop()


app = FastAPI(lifespan=lifespan)


add_routes(app=app)
add_middlewares(app=app)
add_exceptions(app=app)

app.mount("/screenshot", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshot")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.app:app", host="0.0.0.0", port=8000, reload=True)
