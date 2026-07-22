import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import colorlog

# ==========================================
# Iris Logger Setup
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

_file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

# Singletons dla uchwytów plików, zapobiegające wyciekom pamięci i blokadom plików
_console_handler = colorlog.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_color_formatter)

_file_handler = RotatingFileHandler(
    LOG_DIR / "iris.log",
    maxBytes=MAX_LOG_SIZE,
    backupCount=BACKUP_COUNT,
    encoding="utf-8",
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(_file_formatter)

_error_handler = RotatingFileHandler(
    LOG_DIR / "error.log",
    maxBytes=MAX_LOG_SIZE,
    backupCount=BACKUP_COUNT,
    encoding="utf-8",
)
_error_handler.setLevel(logging.ERROR)
_error_handler.setFormatter(_file_formatter)

_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str = "Iris") -> logging.Logger:
    """Zwraca skonsolidowany logger dla podanego modułu."""
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Unikanie wielokrotnego dodawania tych samych handlerów
    if not logger.handlers:
        logger.addHandler(_console_handler)
        logger.addHandler(_file_handler)
        logger.addHandler(_error_handler)

    _loggers[name] = logger
    return logger


# Domyślny logger główny
_default_logger = get_logger("Iris")


# Funkcje pomocnicze wymagane przez zdarzenia w events/
def log_info(message: str) -> None:
    """Zapisuje informację do domyślnego logu."""
    _default_logger.info(message)


def log_warning(message: str) -> None:
    """Zapisuje ostrzeżenie do domyślnego logu."""
    _default_logger.warning(message)


def log_error(message: str, exc_info: bool = False) -> None:
    """Zapisuje błąd do logu błędu i konsoli."""
    _default_logger.error(message, exc_info=exc_info)