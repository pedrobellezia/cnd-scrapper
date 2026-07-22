from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from typing import Tuple
from playwright.async_api import Page, BrowserContext

from app.core import get_tools
from app.services import Estadual
from app.schemas import EstadualRequest

router = APIRouter()


@router.post("")
async def estadual(
    data: EstadualRequest, tools: Tuple[Page, BrowserContext] = Depends(get_tools)
):
    page, context = tools
    result = await Estadual.execute_scrap(
        page=page, context=context, cnpj=data.cnpj, uf=data.uf
    )
    if not result:
        raise HTTPException(status_code=404, detail="UF não suportada.")

    return Response(content=result, media_type="application/pdf")
