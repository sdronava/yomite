"""Unit tests for structured logger utility."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from utils.logger import StructuredLogger  # noqa: E402


class TestStructuredLogger:
    """Test StructuredLogger class."""

    def test_logger_initialization(self):
        """Test logger initialization."""
        logger = StructuredLogger(service_name="test-service")
        assert logger.service_name == "test-service"
        assert logger.log_level == "INFO"

    def test_logger_initialization_with_custom_level(self):
        """Test logger initialization with custom log level."""
        logger = StructuredLogger(service_name="test-service", log_level="DEBUG")
        assert logger.log_level == "DEBUG"

    def test_logger_info(self, caplog):
        """Test logger info method."""
        logger = StructuredLogger(service_name="test-service")
        with caplog.at_level(logging.INFO):
            logger.info("test_event", "Test message", request_id="123")
        assert "Test message" in caplog.text

    def test_logger_error(self, caplog):
        """Test logger error method."""
        logger = StructuredLogger(service_name="test-service")
        with caplog.at_level(logging.ERROR):
            logger.error("test_event", "Error message", request_id="123")
        assert "Error message" in caplog.text

    def test_logger_warning(self, caplog):
        """Test logger warning method."""
        logger = StructuredLogger(service_name="test-service")
        with caplog.at_level(logging.WARNING):
            logger.warning("test_event", "Warning message", request_id="123")
        assert "Warning message" in caplog.text

    def test_logger_debug(self, caplog):
        """Test logger debug method."""
        logger = StructuredLogger(service_name="test-service", log_level="DEBUG")
        with caplog.at_level(logging.DEBUG):
            logger.debug("test_event", "Debug message", request_id="123")
        assert "Debug message" in caplog.text

    def test_logger_sanitize_sensitive_data(self):
        """Test logger sanitizes sensitive data."""
        logger = StructuredLogger(service_name="test-service")
        data = {"password": "secret123", "name": "John"}
        sanitized = logger._sanitize_data(data)
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["name"] == "John"

    def test_logger_sanitize_nested_data(self):
        """Test logger sanitizes nested sensitive data."""
        logger = StructuredLogger(service_name="test-service")
        data = {"user": {"password": "secret123", "name": "John"}}
        sanitized = logger._sanitize_data(data)
        assert sanitized["user"]["password"] == "***REDACTED***"
        assert sanitized["user"]["name"] == "John"

    def test_logger_sanitize_message_password(self):
        """Test logger sanitizes password in messages."""
        logger = StructuredLogger(service_name="test-service")
        message = 'password="secret123"'
        sanitized = logger._sanitize_message(message)
        assert "***REDACTED***" in sanitized

    def test_logger_sanitize_message_token(self):
        """Test logger sanitizes token in messages."""
        logger = StructuredLogger(service_name="test-service")
        message = 'session_token="abc123def456"'
        sanitized = logger._sanitize_message(message)
        assert "***REDACTED***" in sanitized
