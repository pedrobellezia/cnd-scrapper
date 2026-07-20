from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core import logger
from .errors import ScrapError
from app.schemas import ErrorDetails, ErrorResponse


async def request_validation_handler(_: Request, exc: RequestValidationError):
    formatted_errors = {}
    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"] if part != "body")
        formatted_errors[field or "body"] = err["msg"]

    payload = ErrorResponse(
        error="RequestValidationError",
        message="Houve um erro de validação nos dados enviados",
        details=formatted_errors,
    )
    logger.warning("Validation error: %s", payload.model_dump())
    return JSONResponse(status_code=422, content=payload.model_dump())


async def scrap_error_handler(_: Request, exc: ScrapError):
    payload = ErrorResponse(
        error=exc.error_type.value,
        message=exc.message,
        details=ErrorDetails(
            cnpj=exc.cnpj,
            cnd_type=exc.tipo_cnd,
            url=exc.url,
            screenshot=exc.screenshot,
            uf=exc.uf,
            municipio=exc.municipio,
        ),
    )

    logger.error(
        "Scrap error on %s for CNPJ %s: %s",
        exc.tipo_cnd,
        exc.cnpj,
        exc.message,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=exc.status_code, content=payload.model_dump(exclude_none=True)
    )


async def http_exception_handler(_: Request, exc: HTTPException):
    payload = ErrorResponse(
        error="HTTPException",
        message=str(exc.detail),
        details=ErrorDetails(status_code=exc.status_code),
    )
    logger.warning("HTTP exception: %s", payload.model_dump())
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


async def generic_exception_handler(_: Request, exc: Exception):
    payload = ErrorResponse(
        error="InternalServerError",
        message="Ocorreu um erro inesperado",
    )
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(status_code=500, content=payload.model_dump())
