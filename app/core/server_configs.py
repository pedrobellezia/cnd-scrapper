from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from starlette.middleware.cors import CORSMiddleware
from .config import ALLOWED_ORIGINS
from .security import auth_key
from .middleware import add_process_time_header
from app.exceptions import (
    request_validation_handler,
    ScrapError,
    scrap_error_handler,
    http_exception_handler,
    generic_exception_handler,
)
from app.router import (
    trabalhista_router,
    municipal_router,
    fgts_router,
    estadual_router,
)


def add_routes(app: FastAPI):
    app.include_router(
        estadual_router, prefix="/estadual", dependencies=[Depends(auth_key)]
    )
    app.include_router(fgts_router, prefix="/fgts", dependencies=[Depends(auth_key)])
    app.include_router(
        municipal_router, prefix="/municipal", dependencies=[Depends(auth_key)]
    )
    app.include_router(
        trabalhista_router, prefix="/trabalhista", dependencies=[Depends(auth_key)]
    )


def add_middlewares(app: FastAPI):
    app.middleware("http")(add_process_time_header)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS],
        allow_methods=["GET", "POST"],
        allow_headers=[
            "Content-Type",
            "Authorization",
        ],
        allow_credentials=True,
        max_age=600,
    )


def add_exceptions(app: FastAPI):
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(ScrapError, scrap_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
