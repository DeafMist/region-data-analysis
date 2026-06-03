"""Logging configuration for the entire project."""

import logging
import sys
from typing import Optional
from config import LOG_FORMAT, LOG_LEVEL


def setup_logger(name: Optional[str] = None, level: str = LOG_LEVEL) -> logging.Logger:
    """
    Set up a logger with console handler.

    Args:
        name: Logger name (if None, returns root logger)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid adding multiple handlers
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        formatter = logging.Formatter(LOG_FORMAT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
