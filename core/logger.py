import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog

# ==========================================
# Iris Logger
# ==========================================

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_color_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt=DATE_FORMAT,
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)

_file_formatter = logging.Formatter(
    LOG_FORMAT,
    DATE_FORMAT,
)

_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # =============================
    # Console
    # =============================
    console = colorlog.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(_color_formatter)

    # =============================
    # Main log
    # =============================
    file_handler = RotatingFileHandler(
        LOG_DIR / "iris.log",
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_file_formatter)

    # =============================
    # Error log
    # =============================
    error_handler = RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )

    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(_file_formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    _loggers[name] = logger

    return logger