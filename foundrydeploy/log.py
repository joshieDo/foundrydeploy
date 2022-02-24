import sys
from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    colorize=True,
    format="<green>{time}</green> | <level>{level}</level> | {message}",
)


def _info(msg: str):
    logger.info(msg)


def _debug(msg: str):
    logger.debug(msg)


def _error(msg: str):
    logger.error(msg)
