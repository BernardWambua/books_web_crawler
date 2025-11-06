from loguru import logger
import sys
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL, colorize=True,
           format="<green>{time}</green> | <level>{level}</level> | <cyan>{message}</cyan>")

def get_logger():
    return logger
