"""Unit tests for input validator utility."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from utils.input_validator import InputValidator, ValidationError  # noqa: E402


class TestInputValidator:
    """Test InputValidator class."""

    def test_validate_email_valid(self):
        """Test validating valid email."""
        email = InputValidator.validate_email("user@example.com")
        assert email == "user@example.com"

    def test_validate_email_uppercase(self):
        """Test email is converted to lowercase."""
        email = InputValidator.validate_email("User@Example.COM")
        assert email == "user@example.com"

    def test_validate_email_invalid_format(self):
        """Test validating invalid email format."""
        with pytest.raises(ValidationError):
            InputValidator.validate_email("invalid-email")

    def test_validate_email_too_long(self):
        """Test validating email exceeding max length."""
        with pytest.raises(ValidationError):
            InputValidator.validate_email("x" * 255 + "@example.com")

    def test_validate_email_empty(self):
        """Test validating empty email."""
        with pytest.raises(ValidationError):
            InputValidator.validate_email("")

    def test_validate_provider_valid(self):
        """Test validating valid provider."""
        provider = InputValidator.validate_provider("google")
        assert provider == "google"

    def test_validate_provider_uppercase(self):
        """Test provider is converted to lowercase."""
        provider = InputValidator.validate_provider("GOOGLE")
        assert provider == "google"

    def test_validate_provider_unsupported(self):
        """Test validating unsupported provider."""
        with pytest.raises(ValidationError):
            InputValidator.validate_provider("twitter")

    def test_sanitize_string_valid(self):
        """Test sanitizing valid string."""
        result = InputValidator.sanitize_string("  Hello World  ")
        assert result == "Hello World"

    def test_sanitize_string_too_long(self):
        """Test sanitizing string exceeding max length."""
        with pytest.raises(ValidationError):
            InputValidator.sanitize_string("x" * 1001)

    def test_sanitize_string_removes_control_chars(self):
        """Test sanitizing removes control characters."""
        result = InputValidator.sanitize_string("Hello\x00World")
        assert "\x00" not in result

    def test_detect_injection_script_tag(self):
        """Test detecting script tag injection."""
        with pytest.raises(ValidationError):
            InputValidator.detect_injection("<script>alert('xss')</script>")

    def test_detect_injection_javascript_protocol(self):
        """Test detecting javascript protocol injection."""
        with pytest.raises(ValidationError):
            InputValidator.detect_injection("javascript:alert('xss')")

    def test_detect_injection_event_handler(self):
        """Test detecting event handler injection."""
        with pytest.raises(ValidationError):
            InputValidator.detect_injection("<img onerror=alert('xss')>")

    def test_validate_session_token_valid(self):
        """Test validating valid session token."""
        token = InputValidator.validate_session_token("v1.abcdef123456")
        assert token == "v1.abcdef123456"

    def test_validate_session_token_invalid_format(self):
        """Test validating token with invalid format."""
        with pytest.raises(ValidationError):
            InputValidator.validate_session_token("invalid_token")

    def test_validate_session_token_too_short(self):
        """Test validating token that is too short."""
        with pytest.raises(ValidationError):
            InputValidator.validate_session_token("v1.abc")

    def test_validate_redirect_uri_valid_https(self):
        """Test validating valid HTTPS redirect URI."""
        uri = InputValidator.validate_redirect_uri("https://example.com/callback")
        assert uri == "https://example.com/callback"

    def test_validate_redirect_uri_valid_http(self):
        """Test validating valid HTTP redirect URI."""
        uri = InputValidator.validate_redirect_uri("http://localhost:3000/callback")
        assert uri == "http://localhost:3000/callback"

    def test_validate_redirect_uri_invalid_protocol(self):
        """Test validating URI with invalid protocol."""
        with pytest.raises(ValidationError):
            InputValidator.validate_redirect_uri("ftp://example.com/callback")

    def test_validate_oauth_code_valid(self):
        """Test validating valid OAuth code."""
        code = InputValidator.validate_oauth_code("auth_code_1234567890")
        assert code == "auth_code_1234567890"

    def test_validate_oauth_code_too_short(self):
        """Test validating OAuth code that is too short."""
        with pytest.raises(ValidationError):
            InputValidator.validate_oauth_code("short")

    def test_validate_oauth_code_too_long(self):
        """Test validating OAuth code that is too long."""
        with pytest.raises(ValidationError):
            InputValidator.validate_oauth_code("x" * 1001)
