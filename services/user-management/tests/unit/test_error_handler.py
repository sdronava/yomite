"""Unit tests for error handler utility."""

import sys
import os
import pytest
from unittest.mock import Mock, patch
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
        error = APIError(
            code=ErrorCodes.VALIDATION_ERROR, message="Invalid input", details={"field": "name"}
        )
        response = create_api_error_response(error, "req-123")
        assert response["error"]["details"] == {"field": "name"}
