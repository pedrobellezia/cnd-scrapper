from __future__ import annotations

from enum import Enum


class ErrorType(Enum):
    ElementNotFound = "ElementNotFound"
    TimeoutError = "TimeoutError"
    DownloadError = "DownloadError"
    ScrapError = "ScrapError"
    CaptchaError = "CaptchaError"
    CndUnavailable = "CndUnavailable"


class AppBaseError(Exception):
    status_code = 500

    def __init__(
        self,
        message: str | None = None,
        *,
        cnpj: str | None = None,
        tipo_cnd: str | None = None,
        error_type: ErrorType | None = None,
    ):
        self.message = message or "Ocorreu um erro inesperado"
        self.cnpj = cnpj
        self.tipo_cnd = tipo_cnd
        self.error_type = error_type or ErrorType.ScrapError
        super().__init__(self.message)


class ScrapError(AppBaseError):
    status_code = 500

    def __init__(
        self, *, url: str | None = None, error_type: ErrorType | None = None, **kwargs
    ):
        super().__init__(error_type=error_type, **kwargs)
        self.url = url
