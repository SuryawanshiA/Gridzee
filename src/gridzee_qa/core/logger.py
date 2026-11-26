"""Logging setup.

Every class gets its logger with ``get_logger(name)``. Logs go to the console
and to ``reports/framework.log``. Never log passwords or tokens.
"""

import logging
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_LOG_FILE = _ROOT / "reports" / "framework.log"
_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_ROOT_LOGGER_NAME = "gridzee"
_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8", delay=True)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger named ``gridzee.<name>``."""
    _configure()
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
