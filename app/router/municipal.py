from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core import get_tools
from app.services.municipal import Municipal
from app.schemas import MunicipalRequest

router = APIRouter()


@router.post("")
async def municipal(
    data: MunicipalRequest,
    tools=Depends(get_tools),
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
        return Response(
            content="Município não suportado.", media_type="text/plain", status_code=404
        )

    return Response(content=result, media_type="application/pdf")
