"""Structured logging utilities with sensitive data sanitization."""

import json
import logging
import os
import re
from typing import Any, Dict, Optional
from datetime import datetime


class StructuredLogger:
    """Structured JSON logger with sensitive data sanitization."""

    # Patterns for sensitive data
    SENSITIVE_PATTERNS = [
        (re.compile(r'(session_?token["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)', re.IGNORECASE), r"\1***REDACTED***"),
        (re.compile(r'(access_?token["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)', re.IGNORECASE), r"\1***REDACTED***"),
        (re.compile(r'(refresh_?token["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)', re.IGNORECASE), r"\1***REDACTED***"),
        (re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)', re.IGNORECASE), r"\1***REDACTED***"),
        (re.compile(r'(secret["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)', re.IGNORECASE), r"\1***REDACTED***"),
        (re.compile(r'(api_?key["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)', re.IGNORECASE), r"\1***REDACTED***"),
        (re.compile(r'(client_?secret["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)', re.IGNORECASE), r"\1***REDACTED***"),
        (re.compile(r'(authorization["\']?\s*[:=]\s*["\']?Bearer\s+)([^"\'}\s]+)', re.IGNORECASE), r"\1***REDACTED***"),
    ]

    def __init__(self, service_name: str, log_level: Optional[str] = None):
        """
        Initialize structured logger.

        Args:
            service_name: Name of the service (e.g., 'registration-handler')
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.service_name = service_name
        self.log_level = log_level or os.getenv("LOG_LEVEL", "INFO")

        # Configure Python logger
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, self.log_level.upper()))

        # Remove existing handlers
        self.logger.handlers = []

        # Add console handler with JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def _sanitize_message(self, message: str) -> str:
        """
        Remove sensitive data from log message.

        Args:
            message: Log message to sanitize

        Returns:
            Sanitized message
        """
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = pattern.sub(replacement, message)
        return message

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive data from structured data.

        Args:
            data: Data dictionary to sanitize

        Returns:
            Sanitized data dictionary
        """
        sanitized = {}
        sensitive_keys = {
            "session_token",
            "sessionToken",
            "access_token",
            "accessToken",
            "refresh_token",
            "refreshToken",
            "password",
            "secret",
            "api_key",
            "apiKey",
            "client_secret",
            "clientSecret",
            "authorization",
        }

        for key, value in data.items():
            if key.lower() in {k.lower() for k in sensitive_keys}:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_message(value)
            else:
                sanitized[key] = value

        return sanitized

    def _log(self, level: str, event: str, message: str, **kwargs: Any) -> None:
        """
        Internal log method.

        Args:
            level: Log level
            event: Event type
            message: Log message
            **kwargs: Additional structured data
        """
        # Build structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "service": self.service_name,
            "event": event,
            "message": self._sanitize_message(message),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
        }

        # Add sanitized additional data
        if kwargs:
            log_entry["data"] = self._sanitize_data(kwargs)

        # Log as JSON
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_entry))

    def debug(self, event: str, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log("DEBUG", event, message, **kwargs)

    def info(self, event: str, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log("INFO", event, message, **kwargs)

    def warning(self, event: str, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log("WARNING", event, message, **kwargs)

    def error(self, event: str, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log("ERROR", event, message, **kwargs)

    def critical(self, event: str, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log("CRITICAL", event, message, **kwargs)


def get_logger(service_name: str) -> StructuredLogger:
    """
    Get or create a structured logger for a service.

    Args:
        service_name: Name of the service

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(service_name)
