from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ErrorDetails(BaseModel):
    cnpj: str | None = None
    cnd_type: str | None = None
    url: str | None = None
    status_code: int | None = None
    screenshot: str | None = None
    uf: str | None = None
    municipio: str | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    error: str
    message: str
    details: ErrorDetails | dict[str, str] | None = None
