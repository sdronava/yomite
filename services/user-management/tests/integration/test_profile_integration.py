"""Integration tests for profile handler with DynamoDB Local."""

import json
import os
import sys
import pytest
import boto3
from moto import mock_aws

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Set environment variables before importing handler
os.environ["DYNAMODB_TABLE_NAME"] = "yomite-user-data-test"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "INFO"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

from handlers.profile_handler import lambda_handler  # noqa: E402


class MockContext:
    """Mock Lambda context."""

    def __init__(self):
        self.request_id = "test-request-id"
        self.function_name = "test-function"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"


@pytest.fixture
def dynamodb_table():
    """Create DynamoDB table for testing."""
    with mock_aws():
        # Create DynamoDB client
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create table
        table = dynamodb.create_table(
            TableName="yomite-user-data-test",
            KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}, {"AttributeName": "SK", "KeyType": "RANGE"}],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Wait for table to be created
        table.meta.client.get_waiter("table_exists").wait(TableName="yomite-user-data-test")

        yield table


@pytest.fixture
def cognito_event():
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
                        "picture": "https://example.com/picture.jpg",
                    }
                }
            },
            "requestId": "test-request-id",
        }
    }


def test_get_profile_creates_new_profile(dynamodb_table, cognito_event):
    """Test GET /profile creates a new profile from Cognito data."""
    # Execute handler
    response = lambda_handler(cognito_event, MockContext())

    # Verify response
    assert response["statusCode"] == 200
    assert "X-Request-ID" in response["headers"]

    body = json.loads(response["body"])
    assert body["success"] is True
    assert body["data"]["user_id"] == "test-user-123"
    assert body["data"]["email"] == "test@example.com"
    assert body["data"]["name"] == "Test User"
    assert body["data"]["picture_url"] == "https://example.com/picture.jpg"
    assert body["data"]["preferences"] == {}
    assert "created_at" in body["data"]
    assert "updated_at" in body["data"]

    # Verify profile was saved to DynamoDB
    item = dynamodb_table.get_item(Key={"PK": "USER#test-user-123", "SK": "PROFILE"})
    assert "Item" in item
    assert item["Item"]["email"] == "test@example.com"


def test_get_profile_retrieves_existing_profile(dynamodb_table, cognito_event):
    """Test GET /profile retrieves existing profile."""
    # Create existing profile
    dynamodb_table.put_item(
        Item={
            "PK": "USER#test-user-123",
            "SK": "PROFILE",
            "user_id": "test-user-123",
            "email": "test@example.com",
            "name": "Existing User",
            "picture_url": "https://example.com/old-picture.jpg",
            "preferences": {"theme": "dark"},
            "created_at": 1234567890,
            "updated_at": 1234567890,
        }
    )

    # Execute handler
    response = lambda_handler(cognito_event, MockContext())

    # Verify response
    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["success"] is True
    assert body["data"]["name"] == "Existing User"
    assert body["data"]["preferences"] == {"theme": "dark"}
    assert body["data"]["created_at"] == 1234567890


def test_update_profile_creates_new_profile(dynamodb_table, cognito_event):
    """Test PUT /profile creates new profile if it doesn't exist."""
    # Modify event for PUT request
    cognito_event["requestContext"]["http"]["method"] = "PUT"
    cognito_event["body"] = json.dumps({"name": "Updated Name", "preferences": {"theme": "light"}})

    # Execute handler
    response = lambda_handler(cognito_event, MockContext())

    # Verify response
    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["success"] is True
    assert body["data"]["name"] == "Updated Name"
    assert body["data"]["preferences"] == {"theme": "light"}

    # Verify profile was saved to DynamoDB
    item = dynamodb_table.get_item(Key={"PK": "USER#test-user-123", "SK": "PROFILE"})
    assert "Item" in item
    assert item["Item"]["name"] == "Updated Name"


def test_update_profile_updates_existing_profile(dynamodb_table, cognito_event):
    """Test PUT /profile updates existing profile."""
    # Create existing profile
    dynamodb_table.put_item(
        Item={
            "PK": "USER#test-user-123",
            "SK": "PROFILE",
            "user_id": "test-user-123",
            "email": "test@example.com",
            "name": "Original Name",
            "picture_url": "https://example.com/picture.jpg",
            "preferences": {"theme": "dark", "language": "en"},
            "created_at": 1234567890,
            "updated_at": 1234567890,
        }
    )

    # Modify event for PUT request
    cognito_event["requestContext"]["http"]["method"] = "PUT"
    cognito_event["body"] = json.dumps({"name": "Updated Name", "preferences": {"theme": "light"}})

    # Execute handler
    response = lambda_handler(cognito_event, MockContext())

    # Verify response
    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["success"] is True
    assert body["data"]["name"] == "Updated Name"
    # Preferences should be merged
    assert body["data"]["preferences"]["theme"] == "light"
    assert body["data"]["preferences"]["language"] == "en"
    assert body["data"]["updated_at"] > 1234567890

    # Verify profile was updated in DynamoDB
    item = dynamodb_table.get_item(Key={"PK": "USER#test-user-123", "SK": "PROFILE"})
    assert item["Item"]["name"] == "Updated Name"


def test_profile_lifecycle(dynamodb_table, cognito_event):
    """Test complete profile lifecycle: create, read, update."""
    # Step 1: GET profile (creates new profile)
    response = lambda_handler(cognito_event, MockContext())
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["data"]["name"] == "Test User"
    created_at = body["data"]["created_at"]

    # Step 2: GET profile again (retrieves existing)
    response = lambda_handler(cognito_event, MockContext())
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["data"]["created_at"] == created_at

    # Step 3: UPDATE profile
    cognito_event["requestContext"]["http"]["method"] = "PUT"
    cognito_event["body"] = json.dumps({"name": "Updated User", "preferences": {"theme": "dark"}})

    response = lambda_handler(cognito_event, MockContext())
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["data"]["name"] == "Updated User"
    assert body["data"]["preferences"]["theme"] == "dark"
    assert body["data"]["updated_at"] > created_at

    # Step 4: GET profile again (retrieves updated)
    cognito_event["requestContext"]["http"]["method"] = "GET"
    del cognito_event["body"]

    response = lambda_handler(cognito_event, MockContext())
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["data"]["name"] == "Updated User"
    assert body["data"]["preferences"]["theme"] == "dark"


def test_missing_cognito_claims(dynamodb_table):
    """Test request without Cognito claims returns 401."""
    event = {"requestContext": {"http": {"method": "GET"}, "requestId": "test-request-id"}}

    response = lambda_handler(event, MockContext())

    assert response["statusCode"] == 401
    body = json.loads(response["body"])
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_invalid_http_method(dynamodb_table, cognito_event):
    """Test unsupported HTTP method returns 405."""
    cognito_event["requestContext"]["http"]["method"] = "DELETE"

    response = lambda_handler(cognito_event, MockContext())

    assert response["statusCode"] == 405
    body = json.loads(response["body"])
    assert body["success"] is False
    assert "not allowed" in body["error"]["message"]


def test_invalid_json_body(dynamodb_table, cognito_event):
    """Test invalid JSON in request body returns 400."""
    cognito_event["requestContext"]["http"]["method"] = "PUT"
    cognito_event["body"] = "invalid json {"

    response = lambda_handler(cognito_event, MockContext())

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_INPUT"
