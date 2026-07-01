from .estadual import router as estadual_router
from .municipal import router as municipal_router
from .trabalhista import router as trabalhista_router
from .fgts import router as fgts_router

__all__ = [
    "estadual_router",
    "municipal_router",
    "trabalhista_router",
    "fgts_router",
]
