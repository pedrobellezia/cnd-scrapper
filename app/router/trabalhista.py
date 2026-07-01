from fastapi import APIRouter, Depends
from fastapi.responses import Response
from typing import Tuple
from playwright.async_api import Page, BrowserContext

from app.services.trabalhista import Trabalhista
from app.core import get_tools
from app.schemas import BaseCndRequest

router = APIRouter()


@router.post("")
async def trabalhista(
    data: BaseCndRequest, tools: Tuple[Page, BrowserContext] = Depends(get_tools)
) -> Response:
    page, context = tools
    pdf_bytes = await Trabalhista.execute_scrap(page=page, cnpj=data.cnpj)
    return Response(content=pdf_bytes, media_type="application/pdf")
