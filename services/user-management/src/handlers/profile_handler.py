"""Lambda handler for user profile operations."""

import json
import os
import time
from typing import Dict, Any

from models.entities import CognitoUserContext, UserProfile, APIResponse, APIError
from models.error_codes import ErrorCodes
from utils.logger import StructuredLogger
from utils.dynamodb_client import DynamoDBClient
from utils.error_handler import handle_dynamodb_error
from utils.monitoring import (
    trace_function,
    track_operation,
    add_trace_annotation,
    add_trace_metadata,
    track_cognito_authorization,
    track_cognito_authorization_failure,
)

# Initialize logger
logger = StructuredLogger(service_name="user-profile-handler")

# Initialize DynamoDB client (reused across invocations)
dynamodb_client = None


def get_dynamodb_client() -> DynamoDBClient:
    """Get or create DynamoDB client (cached in global scope)."""
    global dynamodb_client
    if dynamodb_client is None:
        table_name = os.environ.get("DYNAMODB_TABLE_NAME")
        endpoint_url = os.environ.get("DYNAMODB_ENDPOINT_URL")  # For local testing
        dynamodb_client = DynamoDBClient(table_name, endpoint_url=endpoint_url)
    return dynamodb_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user profile operations (GET, PUT).

    Args:
        event: API Gateway event with Cognito authorizer context
        context: Lambda execution context

    Returns:
        API Gateway response with status code and body
    """
    request_id = context.request_id if hasattr(context, "request_id") else "local"
    http_method = event.get("requestContext", {}).get("http", {}).get("method", "UNKNOWN")

    # Add X-Ray annotations
    add_trace_annotation("request_id", request_id)
    add_trace_annotation("http_method", http_method)

    logger.info("profile_request", "Profile request received", request_id=request_id, method=http_method)

    try:
        # Extract Cognito user context from API Gateway authorizer
        authorizer_claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})

        if not authorizer_claims:
            logger.warning("missing_cognito_claims", "No Cognito claims found in request", request_id=request_id)
            track_cognito_authorization_failure("MissingClaims")
            return format_error_response(
                status_code=401,
                error_code=ErrorCodes.UNAUTHORIZED,
                message="Authentication required",
                request_id=request_id,
            )

        # Track successful authorization
        track_cognito_authorization()

        user_context = CognitoUserContext.from_authorizer_claims(authorizer_claims)

        # Add user context to trace
        add_trace_annotation("user_id", user_context.sub)
        add_trace_metadata("user_email", user_context.email)

        # Route to appropriate handler
        if http_method == "GET":
            return handle_get_profile(user_context, request_id)
        elif http_method == "PUT":
            body = json.loads(event.get("body", "{}"))
            return handle_update_profile(user_context, body, request_id)
        else:
            return format_error_response(
                status_code=405,
                error_code=ErrorCodes.VALIDATION_ERROR,
                message=f"Method {http_method} not allowed",
                request_id=request_id,
            )

    except json.JSONDecodeError as e:
        logger.error("invalid_json", "Invalid JSON in request body", request_id=request_id, error=str(e))
        return format_error_response(
            status_code=400,
            error_code=ErrorCodes.INVALID_INPUT,
            message="Invalid JSON in request body",
            request_id=request_id,
        )

    except Exception as e:
        logger.error("unexpected_error", "Unexpected error in profile handler", request_id=request_id, error=str(e))
        return format_error_response(
            status_code=500,
            error_code=ErrorCodes.SERVER_ERROR,
            message="An unexpected error occurred",
            request_id=request_id,
        )


@trace_function("get_profile")
@track_operation("GetProfile", {"Operation": "Read"})
def handle_get_profile(user_context: CognitoUserContext, request_id: str) -> Dict[str, Any]:
    """
    Get user profile from DynamoDB.

    Args:
        user_context: Cognito user context from JWT
        request_id: Request ID for tracing

    Returns:
        API Gateway response with profile data
    """
    try:
        db_client = get_dynamodb_client()

        # Query DynamoDB for user profile
        key = {"PK": f"USER#{user_context.sub}", "SK": "PROFILE"}

        item = db_client.get_item(key)

        if item:
            # Profile exists, return it
            profile = UserProfile.from_dynamodb_item(item)
            logger.info("profile_retrieved", "Profile retrieved", request_id=request_id, user_id=user_context.sub)

            return format_success_response(
                status_code=200,
                data={
                    "user_id": profile.user_id,
                    "email": profile.email,
                    "name": profile.name,
                    "picture_url": profile.picture_url,
                    "preferences": profile.preferences,
                    "created_at": profile.created_at,
                    "updated_at": profile.updated_at,
                },
                request_id=request_id,
            )
        else:
            # Profile doesn't exist, create default from Cognito data
            now = int(time.time())
            profile = UserProfile(
                user_id=user_context.sub,
                email=user_context.email,
                name=user_context.name,
                picture_url=user_context.picture,
                preferences={},
                created_at=now,
                updated_at=now,
            )

            # Save to DynamoDB
            db_client.put_item(profile.to_dynamodb_item())

            logger.info(
                "profile_created", "Profile created from Cognito data", request_id=request_id, user_id=user_context.sub
            )

            return format_success_response(
                status_code=200,
                data={
                    "user_id": profile.user_id,
                    "email": profile.email,
                    "name": profile.name,
                    "picture_url": profile.picture_url,
                    "preferences": profile.preferences,
                    "created_at": profile.created_at,
                    "updated_at": profile.updated_at,
                },
                request_id=request_id,
            )

    except Exception as e:
        logger.error(
            "profile_retrieval_error",
            "Error retrieving profile",
            request_id=request_id,
            user_id=user_context.sub,
            error=str(e),
        )

        return handle_dynamodb_error(e, request_id)


@trace_function("update_profile")
@track_operation("UpdateProfile", {"Operation": "Write"})
def handle_update_profile(user_context: CognitoUserContext, body: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Update user profile in DynamoDB.

    Args:
        user_context: Cognito user context from JWT
        body: Request body with profile updates
        request_id: Request ID for tracing

    Returns:
        API Gateway response with updated profile
    """
    try:
        db_client = get_dynamodb_client()

        # Get existing profile or create new one
        key = {"PK": f"USER#{user_context.sub}", "SK": "PROFILE"}

        existing_item = db_client.get_item(key)

        if existing_item:
            profile = UserProfile.from_dynamodb_item(existing_item)
        else:
            # Create new profile
            now = int(time.time())
            profile = UserProfile(
                user_id=user_context.sub,
                email=user_context.email,
                name=user_context.name,
                picture_url=user_context.picture,
                preferences={},
                created_at=now,
                updated_at=now,
            )

        # Update allowed fields
        if "name" in body:
            profile.name = body["name"]
        if "picture_url" in body:
            profile.picture_url = body["picture_url"]
        if "preferences" in body:
            profile.preferences.update(body["preferences"])

        profile.updated_at = int(time.time())

        # Save to DynamoDB
        db_client.put_item(profile.to_dynamodb_item())

        logger.info("profile_updated", "Profile updated", request_id=request_id, user_id=user_context.sub)

        return format_success_response(
            status_code=200,
            data={
                "user_id": profile.user_id,
                "email": profile.email,
                "name": profile.name,
                "picture_url": profile.picture_url,
                "preferences": profile.preferences,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
            },
            request_id=request_id,
        )

    except Exception as e:
        logger.error(
            "profile_update_error",
            "Error updating profile",
            request_id=request_id,
            user_id=user_context.sub,
            error=str(e),
        )

        return handle_dynamodb_error(e, request_id)


def format_success_response(status_code: int, data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """Format successful API Gateway response."""
    response = APIResponse(success=True, data=data, request_id=request_id)

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "X-Request-ID": request_id},
        "body": json.dumps({"success": response.success, "data": response.data, "request_id": response.request_id}),
    }


def format_error_response(
    status_code: int, error_code: str, message: str, request_id: str, details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Format error API Gateway response."""
    error = APIError(code=error_code, message=message, details=details)

    response = APIResponse(success=False, error=error, request_id=request_id)

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "X-Request-ID": request_id},
        "body": json.dumps(
            {
                "success": response.success,
                "error": {
                    "code": response.error.code,
                    "message": response.error.message,
                    "details": response.error.details,
                },
                "request_id": response.request_id,
            }
        ),
    }
