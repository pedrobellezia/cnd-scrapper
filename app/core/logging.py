import logging
import logging.config
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_traceback
import fastapi
import starlette
import playwright
install_traceback()


class RichHandlerWrapper(RichHandler):
    def __init__(self, **kwargs):
        console = Console(width=160)
        # Suprime traceback do fastapi, starlette e playwright
        kwargs.setdefault(
            "tracebacks_suppress", [fastapi, starlette, playwright]
        )
        super().__init__(console=console, **kwargs)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "app.core.logging.RichHandlerWrapper",
            "level": "DEBUG",
            "show_time": False,
        }
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console"],
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        }
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)


logger = logging.getLogger("app")

