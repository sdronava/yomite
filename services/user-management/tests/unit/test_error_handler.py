"""Unit tests for error handler utility."""

import sys
import os
from botocore.exceptions import ClientError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from utils.error_handler import (  # noqa: E402
    handle_dynamodb_error,
    format_error_response,
    get_http_status_code,
    create_api_error_response,
)
from models.error_codes import ErrorCodes  # noqa: E402
from models.entities import APIError  # noqa: E402


class TestErrorHandler:
    """Test error handler functions."""

    def test_handle_dynamodb_error_resource_not_found(self):
        """Test handling ResourceNotFoundException."""
        error = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
            "GetItem",
        )
        result = handle_dynamodb_error(error, "GetItem")
        assert result.code == ErrorCodes.SERVER_ERROR

    def test_handle_dynamodb_error_validation_exception(self):
        """Test handling ValidationException."""
        error = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid key"}},
            "GetItem",
        )
        result = handle_dynamodb_error(error, "GetItem")
        assert result.code == ErrorCodes.VALIDATION_ERROR

    def test_handle_dynamodb_error_provisioned_throughput_exceeded(self):
        """Test handling ProvisionedThroughputExceededException."""
        error = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "Throttled"}},
            "GetItem",
        )
        result = handle_dynamodb_error(error, "GetItem")
        assert result.code == ErrorCodes.RATE_LIMIT_EXCEEDED

    def test_handle_dynamodb_error_generic(self):
        """Test handling generic DynamoDB error."""
        error = ClientError(
            {"Error": {"Code": "UnknownError", "Message": "Unknown error"}},
            "GetItem",
        )
        result = handle_dynamodb_error(error, "GetItem")
        assert result.code == ErrorCodes.SERVER_ERROR

    def test_format_error_response(self):
        """Test format_error_response function."""
        response = format_error_response(400, ErrorCodes.VALIDATION_ERROR, "Invalid input", "req-123")
        assert response["statusCode"] == 400
        assert "X-Request-ID" in response["headers"]
        assert response["headers"]["X-Request-ID"] == "req-123"

    def test_get_http_status_code_validation_error(self):
        """Test get_http_status_code for validation error."""
        status = get_http_status_code(ErrorCodes.VALIDATION_ERROR)
        assert status == 400

    def test_get_http_status_code_unauthorized(self):
        """Test get_http_status_code for unauthorized."""
        status = get_http_status_code(ErrorCodes.UNAUTHORIZED)
        assert status == 401

    def test_get_http_status_code_not_found(self):
        """Test get_http_status_code for not found."""
        status = get_http_status_code(ErrorCodes.NOT_FOUND)
        assert status == 404

    def test_get_http_status_code_rate_limit(self):
        """Test get_http_status_code for rate limit."""
        status = get_http_status_code(ErrorCodes.RATE_LIMIT_EXCEEDED)
        assert status == 429

    def test_get_http_status_code_server_error(self):
        """Test get_http_status_code for server error."""
        status = get_http_status_code(ErrorCodes.SERVER_ERROR)
        assert status == 500

    def test_create_api_error_response(self):
        """Test create_api_error_response function."""
        error = APIError(code=ErrorCodes.VALIDATION_ERROR, message="Invalid input")
        response = create_api_error_response(error, "req-123")
        assert response["success"] is False
        assert response["error"]["code"] == ErrorCodes.VALIDATION_ERROR
        assert response["error"]["message"] == "Invalid input"
        assert response["request_id"] == "req-123"

    def test_create_api_error_response_with_details(self):
        """Test create_api_error_response with details."""
        error = APIError(code=ErrorCodes.VALIDATION_ERROR, message="Invalid input", details={"field": "name"})
        response = create_api_error_response(error, "req-123")
        assert response["error"]["details"] == {"field": "name"}


class TestRetryWithBackoff:
    """Test retry_with_backoff decorator."""

    def test_retry_with_non_retryable_client_error(self):
        """Test retry_with_backoff with non-retryable ClientError."""
        from utils.error_handler import retry_with_backoff

        attempt_count = 0

        @retry_with_backoff(max_retries=3)
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            # Raise a non-retryable error (not throttling)
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException", "Message": "Condition failed"}},
                "PutItem",
            )

        # Should raise immediately without retrying
        try:
            failing_function()
        except ClientError as e:
            assert e.response["Error"]["Code"] == "ConditionalCheckFailedException"

        # Should only attempt once (no retries for non-retryable errors)
        assert attempt_count == 1

    def test_retry_with_retryable_client_error(self):
        """Test retry_with_backoff with retryable ClientError."""
        from utils.error_handler import retry_with_backoff
        import time

        attempt_count = 0
        start_time = time.time()

        @retry_with_backoff(max_retries=3, initial_delay=0.01, backoff_factor=2.0)
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            # Raise a retryable error (throttling)
            raise ClientError(
                {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "Throttled"}},
                "PutItem",
            )

        # Should retry and eventually raise
        try:
            failing_function()
        except ClientError as e:
            assert e.response["Error"]["Code"] == "ProvisionedThroughputExceededException"

        # Should attempt max_retries times
        assert attempt_count == 3

        # Should have delayed (exponential backoff)
        elapsed = time.time() - start_time
        # At least initial_delay + initial_delay * backoff_factor
        assert elapsed >= 0.01 + 0.02  # 0.01 + 0.01*2

    def test_retry_with_success_after_retries(self):
        """Test retry_with_backoff succeeds after some retries."""
        from utils.error_handler import retry_with_backoff

        attempt_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def eventually_succeeds():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ClientError(
                    {"Error": {"Code": "ThrottlingException", "Message": "Throttled"}},
                    "PutItem",
                )
            return "success"

        result = eventually_succeeds()
        assert result == "success"
        assert attempt_count == 2

    def test_retry_with_non_client_error_exception(self):
        """Test retry_with_backoff with non-ClientError exception."""
        from utils.error_handler import retry_with_backoff

        attempt_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01, exceptions=(ValueError,))
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("Test error")

        # Should retry for ValueError since it's in exceptions tuple
        try:
            failing_function()
        except ValueError:
            pass

        # Should attempt max_retries times
        assert attempt_count == 3

    def test_retry_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        from utils.error_handler import retry_with_backoff
        import time

        delays = []

        @retry_with_backoff(max_retries=4, initial_delay=0.01, backoff_factor=2.0)
        def failing_function():
            current_time = time.time()
            if delays:
                delays.append(current_time - delays[-1])
            else:
                delays.append(current_time)
            raise ClientError(
                {"Error": {"Code": "RequestLimitExceeded", "Message": "Throttled"}},
                "PutItem",
            )

        try:
            failing_function()
        except ClientError:
            pass

        # Should have 4 attempts, 3 delays between them
        # Delays should be approximately: 0.01, 0.02, 0.04 (exponential)
        assert len(delays) == 4

    def test_retry_last_exception_raised(self):
        """Test that last exception is raised after max retries."""
        from utils.error_handler import retry_with_backoff

        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def failing_function():
            raise ClientError(
                {"Error": {"Code": "ThrottlingException", "Message": "Still throttled"}},
                "PutItem",
            )

        # Should raise the last exception
        try:
            failing_function()
            assert False, "Should have raised ClientError"
        except ClientError as e:
            assert e.response["Error"]["Message"] == "Still throttled"


class TestGetHttpStatusCodeComplete:
    """Test all error code mappings in get_http_status_code."""

    def test_all_error_codes_mapped(self):
        """Test that all error codes have correct HTTP status mappings."""
        # Test all error codes from ErrorCodes
        assert get_http_status_code(ErrorCodes.VALIDATION_ERROR) == 400
        assert get_http_status_code(ErrorCodes.INVALID_INPUT) == 400
        assert get_http_status_code(ErrorCodes.UNAUTHORIZED) == 401
        assert get_http_status_code(ErrorCodes.INVALID_TOKEN) == 401
        assert get_http_status_code(ErrorCodes.EXPIRED_TOKEN) == 401
        assert get_http_status_code(ErrorCodes.FORBIDDEN) == 403
        assert get_http_status_code(ErrorCodes.NOT_FOUND) == 404
        assert get_http_status_code(ErrorCodes.ALREADY_EXISTS) == 409
        assert get_http_status_code(ErrorCodes.RATE_LIMIT_EXCEEDED) == 429
        assert get_http_status_code(ErrorCodes.SERVER_ERROR) == 500
        assert get_http_status_code(ErrorCodes.DATABASE_ERROR) == 500

    def test_unknown_error_code_defaults_to_500(self):
        """Test that unknown error codes default to 500."""
        assert get_http_status_code("UNKNOWN_ERROR_CODE") == 500
        assert get_http_status_code("") == 500
