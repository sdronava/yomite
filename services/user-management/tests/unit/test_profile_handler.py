"""Unit tests for profile handler Lambda function."""

import json
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from handlers.profile_handler import lambda_handler, handle_get_profile, handle_update_profile, get_dynamodb_client
from models.entities import CognitoUserContext, UserProfile
from models.error_codes import ErrorCodes


@pytest.fixture
def mock_context():
    """Create mock Lambda context."""
    context = Mock()
    context.request_id = "test-request-123"
    context.get_remaining_time_in_millis = Mock(return_value=30000)
    return context


@pytest.fixture
def mock_cognito_event():
    """Create mock API Gateway event with Cognito authorizer."""
    return {
        "requestContext": {
            "http": {"method": "GET"},
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "test-user-123",
                        "email": "test@example.com",
                        "email_verified": "true",
                        "name": "Test User",
                        "picture": "https://example.com/pic.jpg",
                    }
                }
            },
            "requestId": "test-request-123",
        }
    }


@pytest.fixture
def mock_dynamodb_client():
    """Create mock DynamoDB client."""
    with patch("handlers.profile_handler.get_dynamodb_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestLambdaHandler:
    """Test lambda_handler function."""

    def test_get_profile_success(self, mock_cognito_event, mock_context, mock_dynamodb_client):
        """Test successful GET /profile request."""
        # Setup mock DynamoDB response
        mock_dynamodb_client.get_item.return_value = {
            "PK": "USER#test-user-123",
            "SK": "PROFILE",
            "UserId": "test-user-123",
            "Email": "test@example.com",
            "Name": "Test User",
            "PictureUrl": "https://example.com/pic.jpg",
            "Preferences": {"theme": "dark"},
            "CreatedAt": 1234567890,
            "UpdatedAt": 1234567890,
        }

        # Execute
        response = lambda_handler(mock_cognito_event, mock_context)

        # Verify
        assert response["statusCode"] == 200
        assert "X-Request-ID" in response["headers"]

        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["email"] == "test@example.com"
        assert body["data"]["name"] == "Test User"
        assert body["data"]["preferences"] == {"theme": "dark"}

    def test_get_profile_creates_new_profile(self, mock_cognito_event, mock_context, mock_dynamodb_client):
        """Test GET /profile creates profile from Cognito data when not exists."""
        # Setup mock DynamoDB response (no existing profile)
        mock_dynamodb_client.get_item.return_value = None

        # Execute
        response = lambda_handler(mock_cognito_event, mock_context)

        # Verify
        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["email"] == "test@example.com"
        assert body["data"]["name"] == "Test User"

        # Verify put_item was called to create profile
        mock_dynamodb_client.put_item.assert_called_once()

    def test_put_profile_success(self, mock_cognito_event, mock_context, mock_dynamodb_client):
        """Test successful PUT /profile request."""
        # Setup event for PUT request
        mock_cognito_event["requestContext"]["http"]["method"] = "PUT"
        mock_cognito_event["body"] = json.dumps(
            {"name": "Updated Name", "preferences": {"theme": "light", "language": "en"}}
        )

        # Setup mock DynamoDB response (existing profile)
        mock_dynamodb_client.get_item.return_value = {
            "PK": "USER#test-user-123",
            "SK": "PROFILE",
            "UserId": "test-user-123",
            "Email": "test@example.com",
            "Name": "Test User",
            "Preferences": {"theme": "dark"},
            "CreatedAt": 1234567890,
            "UpdatedAt": 1234567890,
        }

        # Execute
        response = lambda_handler(mock_cognito_event, mock_context)

        # Verify
        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["name"] == "Updated Name"
        assert body["data"]["preferences"]["theme"] == "light"
        assert body["data"]["preferences"]["language"] == "en"

        # Verify put_item was called to update profile
        mock_dynamodb_client.put_item.assert_called_once()

    def test_missing_cognito_claims(self, mock_context):
        """Test request without Cognito claims returns 401."""
        event = {"requestContext": {"http": {"method": "GET"}, "requestId": "test-request-123"}}

        response = lambda_handler(event, mock_context)

        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"]["code"] == ErrorCodes.UNAUTHORIZED

    def test_invalid_http_method(self, mock_cognito_event, mock_context):
        """Test unsupported HTTP method returns 405."""
        mock_cognito_event["requestContext"]["http"]["method"] = "DELETE"

        response = lambda_handler(mock_cognito_event, mock_context)

        assert response["statusCode"] == 405
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"]["code"] == ErrorCodes.VALIDATION_ERROR

    def test_invalid_json_body(self, mock_cognito_event, mock_context):
        """Test invalid JSON in PUT request returns 400."""
        mock_cognito_event["requestContext"]["http"]["method"] = "PUT"
        mock_cognito_event["body"] = "invalid json"

        response = lambda_handler(mock_cognito_event, mock_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"]["code"] == ErrorCodes.INVALID_INPUT


class TestCognitoUserContext:
    """Test CognitoUserContext model."""

    def test_from_authorizer_claims(self):
        """Test creating CognitoUserContext from JWT claims."""
        claims = {
            "sub": "user-123",
            "email": "user@example.com",
            "email_verified": "true",
            "name": "John Doe",
            "picture": "https://example.com/pic.jpg",
        }

        context = CognitoUserContext.from_authorizer_claims(claims)

        assert context.sub == "user-123"
        assert context.email == "user@example.com"
        assert context.email_verified is True
        assert context.name == "John Doe"
        assert context.picture == "https://example.com/pic.jpg"

    def test_from_authorizer_claims_minimal(self):
        """Test creating CognitoUserContext with minimal claims."""
        claims = {"sub": "user-123", "email": "user@example.com"}

        context = CognitoUserContext.from_authorizer_claims(claims)

        assert context.sub == "user-123"
        assert context.email == "user@example.com"
        assert context.email_verified is False
        assert context.name is None
        assert context.picture is None


class TestUserProfile:
    """Test UserProfile model."""

    def test_to_dynamodb_item(self):
        """Test converting UserProfile to DynamoDB item."""
        profile = UserProfile(
            user_id="user-123",
            email="user@example.com",
            name="John Doe",
            picture_url="https://example.com/pic.jpg",
            preferences={"theme": "dark"},
            created_at=1234567890,
            updated_at=1234567890,
        )

        item = profile.to_dynamodb_item()

        assert item["PK"] == "USER#user-123"
        assert item["SK"] == "PROFILE"
        assert item["EntityType"] == "USER_PROFILE"
        assert item["UserId"] == "user-123"
        assert item["Email"] == "user@example.com"
        assert item["Name"] == "John Doe"
        assert item["PictureUrl"] == "https://example.com/pic.jpg"
        assert item["Preferences"] == {"theme": "dark"}
        assert item["CreatedAt"] == 1234567890
        assert item["UpdatedAt"] == 1234567890

    def test_from_dynamodb_item(self):
        """Test creating UserProfile from DynamoDB item."""
        item = {
            "PK": "USER#user-123",
            "SK": "PROFILE",
            "UserId": "user-123",
            "Email": "user@example.com",
            "Name": "John Doe",
            "PictureUrl": "https://example.com/pic.jpg",
            "Preferences": {"theme": "dark"},
            "CreatedAt": 1234567890,
            "UpdatedAt": 1234567890,
        }

        profile = UserProfile.from_dynamodb_item(item)

        assert profile.user_id == "user-123"
        assert profile.email == "user@example.com"
        assert profile.name == "John Doe"
        assert profile.picture_url == "https://example.com/pic.jpg"
        assert profile.preferences == {"theme": "dark"}
        assert profile.created_at == 1234567890
        assert profile.updated_at == 1234567890
