import logging
import os
from functools import lru_cache
from logging.handlers import RotatingFileHandler


# Цвета ANSI
class Color:
    RESET = "\033[0m"
    GREY = "\033[90m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"


# Цветной форматтер
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Color.BLUE,
        logging.INFO: Color.GREEN,
        logging.WARNING: Color.YELLOW,
        logging.ERROR: Color.RED,
        logging.CRITICAL: Color.RED,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, Color.RESET)
        record.levelname = f"{color}{record.levelname}{Color.RESET}"
        return super().format(record)


LOG_FORMAT = (
    "%(asctime)s [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d - %(message)s"
)


@lru_cache(maxsize=None)
def logger_config(name: str, log_file: str, level: int = logging.INFO, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5) -> logging.Logger:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_folder = os.path.abspath(os.path.join(base_dir, "..", "files", "logs"))
    os.makedirs(log_folder, exist_ok=True)

    log_file_path = os.path.join(log_folder, log_file)

    file_formatter = logging.Formatter(LOG_FORMAT)
    console_formatter = ColorFormatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
        delay=True,
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.propagate = False

    return logger
