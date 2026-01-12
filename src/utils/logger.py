"""
Утилиты для логирования
"""
import sys
from pathlib import Path
from loguru import logger
from config.config import config


def setup_logger():
    """Настройка логгера"""
    
    # Удаляем дефолтный handler
    logger.remove()
    
    # Console output
    logger.add(
        sys.stdout,
        level=config.LOG_LEVEL,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # File output
    logger.add(
        config.LOG_FILE,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )
    
    return logger


# Singleton
log = setup_logger()
