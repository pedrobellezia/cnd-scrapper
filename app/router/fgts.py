from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core import get_tools
from app.services import Fgts
from app.schemas import BaseCndRequest

router = APIRouter()


@router.post("")
async def fgts(data: BaseCndRequest, tools=Depends(get_tools)):
    page, context = tools
    pdf_bytes = await Fgts.execute_scrap(page=page, cnpj=data.cnpj)
    return Response(content=pdf_bytes, media_type="application/pdf")
