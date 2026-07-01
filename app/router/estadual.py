from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core import get_tools
from app.services import Estadual
from app.schemas import EstadualRequest

router = APIRouter()


@router.post("")
async def estadual(data: EstadualRequest, tools=Depends(get_tools)):
    page, context = tools
    result = await Estadual.execute_scrap(
        page=page, context=context, cnpj=data.cnpj, uf=data.uf
    )
    if not result:
        return Response(
            content="UF não suportada.", media_type="text/plain", status_code=404
        )

    return Response(content=result, media_type="application/pdf")
