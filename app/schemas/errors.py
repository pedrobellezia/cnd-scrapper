from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ValidationErrorItem(BaseModel):
    field: str
    message: str


class ErrorDetails(BaseModel):
    cnpj: str | None = None
    cnd_type: str | None = None
    url: str | None = None
    status_code: int | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    error: str
    message: str
    details: ErrorDetails | list[ValidationErrorItem] | None = None
