"""Input validation and sanitization utilities."""

import re


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


class InputValidator:
    """Validates and sanitizes user input."""

    # Supported OAuth providers
    SUPPORTED_PROVIDERS = {"google", "facebook", "github"}

    # Email validation regex (RFC 5322 simplified)
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    # Injection detection patterns
    INJECTION_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),  # Event handlers
        re.compile(r"<iframe", re.IGNORECASE),
        re.compile(r"<object", re.IGNORECASE),
        re.compile(r"<embed", re.IGNORECASE),
    ]

    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            Validated email (lowercase)

        Raises:
            ValidationError: If email is invalid
        """
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required")

        email = email.strip().lower()

        if len(email) > 254:  # RFC 5321
            raise ValidationError("Email is too long")

        if not cls.EMAIL_REGEX.match(email):
            raise ValidationError("Invalid email format")

        return email

    @classmethod
    def validate_provider(cls, provider: str) -> str:
        """
        Validate OAuth provider.

        Args:
            provider: Provider name to validate

        Returns:
            Validated provider (lowercase)

        Raises:
            ValidationError: If provider is not supported
        """
        if not provider or not isinstance(provider, str):
            raise ValidationError("Provider is required")

        provider = provider.strip().lower()

        if provider not in cls.SUPPORTED_PROVIDERS:
            raise ValidationError(
                f"Unsupported provider: {provider}. " f"Supported: {', '.join(cls.SUPPORTED_PROVIDERS)}"
            )

        return provider

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string

        Raises:
            ValidationError: If string is invalid
        """
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")

        # Remove null bytes and control characters
        value = "".join(char for char in value if ord(char) >= 32 or char in "\n\r\t")

        # Trim whitespace
        value = value.strip()

        # Check length
        if len(value) > max_length:
            raise ValidationError(f"Value exceeds maximum length of {max_length}")

        return value

    @classmethod
    def detect_injection(cls, value: str) -> None:
        """
        Detect potential injection attacks.

        Args:
            value: String to check

        Raises:
            ValidationError: If injection pattern detected
        """
        if not isinstance(value, str):
            return

        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(value):
                raise ValidationError("Potential injection attack detected")

    @classmethod
    def validate_session_token(cls, token: str) -> str:
        """
        Validate session token format.

        Args:
            token: Session token to validate

        Returns:
            Validated token

        Raises:
            ValidationError: If token format is invalid
        """
        if not token or not isinstance(token, str):
            raise ValidationError("Session token is required")

        token = token.strip()

        # Check format: v1.{base64url}
        if not token.startswith("v1."):
            raise ValidationError("Invalid token format")

        if len(token) < 10:
            raise ValidationError("Token is too short")

        if len(token) > 500:
            raise ValidationError("Token is too long")

        return token

    @classmethod
    def validate_redirect_uri(cls, uri: str) -> str:
        """
        Validate OAuth redirect URI.

        Args:
            uri: Redirect URI to validate

        Returns:
            Validated URI

        Raises:
            ValidationError: If URI is invalid
        """
        if not uri or not isinstance(uri, str):
            raise ValidationError("Redirect URI is required")

        uri = uri.strip()

        # Basic URL validation
        if not uri.startswith(("http://", "https://")):
            raise ValidationError("Redirect URI must be HTTP or HTTPS")

        if len(uri) > 2048:
            raise ValidationError("Redirect URI is too long")

        # Check for injection attempts
        cls.detect_injection(uri)

        return uri

    @classmethod
    def validate_oauth_code(cls, code: str) -> str:
        """
        Validate OAuth authorization code.

        Args:
            code: Authorization code to validate

        Returns:
            Validated code

        Raises:
            ValidationError: If code is invalid
        """
        if not code or not isinstance(code, str):
            raise ValidationError("Authorization code is required")

        code = code.strip()

        if len(code) < 10:
            raise ValidationError("Authorization code is too short")

        if len(code) > 1000:
            raise ValidationError("Authorization code is too long")

        return code
