from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from typing import Tuple
from playwright.async_api import Page, BrowserContext

from app.core import get_tools
from app.services.municipal import Municipal
from app.schemas import MunicipalRequest

router = APIRouter()


@router.post("")
async def municipal(
    data: MunicipalRequest,
    tools: Tuple[Page, BrowserContext] = Depends(get_tools),
):
    page, context = tools
    result = await Municipal._execute_scrap(
        page=page,
        context=context,
        cnpj=data.cnpj,
        uf=data.uf.lower(),
        municipio=data.municipio.lower(),
    )

    if not result:
        raise HTTPException(status_code=404, detail="Município não suportado.")

    return Response(content=result, media_type="application/pdf")
