import re
from unidecode import unidecode
from pydantic import BaseModel, ConfigDict, StrictStr, field_validator


def normalize_cnpj(cnpj: str) -> str:
    cnpj = re.sub(r"\D", "", cnpj)

    if len(cnpj) != 14:
        raise ValueError("CNPJ deve conter exatamente 14 dígitos")

    return cnpj


def normalize_municipio(municipio: str) -> str:
    municipio = unidecode(municipio.strip().lower())
    # Troca " " por _
    municipio = re.sub(r"\s+", "_", municipio)
    # Retira tudo que não seja "a-z" e "_"
    municipio = re.sub(r"[^a-z_]", "", municipio)
    # Retira "_" duplicados e bordas com "_"
    municipio = re.sub(r"_+", "_", municipio).strip("_")

    return municipio


class BaseCndRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    cnpj: StrictStr

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        return normalize_cnpj(v)


class EstadualRequest(BaseCndRequest):
    uf: StrictStr

    @field_validator("uf")
    @classmethod
    def validate_uf(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z]{2}", v):
            raise ValueError("UF deve conter exatamente 2 letras")

        return v.lower()


class MunicipalRequest(EstadualRequest):
    municipio: StrictStr

    @field_validator("municipio")
    @classmethod
    def validate_municipio(cls, v: str) -> str:
        normalized = normalize_municipio(v)
        if not normalized:
            raise ValueError("Municipio invalido")
        return normalized
