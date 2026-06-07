import logging
from datetime import datetime

logger = logging.getLogger("students_app")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(
    f"students_app_{datetime.now().strftime('%Y%m%d')}.log",
    encoding="utf-8",
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def log_info(message: str):
    logger.info(message)


def log_error(message: str):
    logger.error(message)


def log_warning(message: str):
    logger.warning(message)


def log_debug(message: str):
    logger.debug(message)
