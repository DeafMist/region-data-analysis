"""Unit tests for logger module."""

import logging
from utils.logger import setup_logger


class TestLogger:
    """Tests for logger setup."""

    def test_setup_logger_returns_logger(self):
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_setup_logger_level(self):
        logger = setup_logger("test_level", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logger_root(self):
        logger = setup_logger()
        assert logger.name == "root"
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_only_one_handler(self):
        logger = setup_logger("test_handlers")
        initial_count = len(logger.handlers)
        logger2 = setup_logger("test_handlers")
        assert len(logger2.handlers) == initial_count
