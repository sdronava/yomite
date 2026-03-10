"""Error handling utilities for DynamoDB and OAuth operations."""

import time
import functools
from typing import Callable, Any, TypeVar, cast
from botocore.exceptions import ClientError
from src.models.error_codes import ErrorCodes
from src.models.entities import APIError

# Type variable for decorator
F = TypeVar('F', bound=Callable[..., Any])


class OAuthError(Exception):
    """Raised when OAuth operation fails."""
    
    def __init__(self, message: str, provider: str, details: Any = None):
        super().__init__(message)
        self.provider = provider
        self.details = details


class DynamoDBError(Exception):
    """Raised when DynamoDB operation fails."""
    
    def __init__(self, message: str, operation: str, details: Any = None):
        super().__init__(message)
        self.operation = operation
        self.details = details


def handle_dynamodb_error(error: ClientError, operation: str) -> APIError:
    """
    Convert DynamoDB ClientError to APIError.
    
    Args:
        error: Boto3 ClientError
        operation: Operation that failed (e.g., 'PutItem', 'Query')
        
    Returns:
        APIError with appropriate code and message
    """
    error_code = error.response['Error']['Code']
    error_message = error.response['Error']['Message']
    
    if error_code == 'ProvisionedThroughputExceededException':
        return APIError(
            code=ErrorCodes.RATE_LIMIT_EXCEEDED,
            message="Service is temporarily unavailable. Please try again.",
            details={'operation': operation, 'error': error_code}
        )
    elif error_code == 'ResourceNotFoundException':
        return APIError(
            code=ErrorCodes.SERVER_ERROR,
            message="Database resource not found",
            details={'operation': operation}
        )
    elif error_code == 'ValidationException':
        return APIError(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Invalid request parameters",
            details={'operation': operation, 'message': error_message}
        )
    else:
        return APIError(
            code=ErrorCodes.SERVER_ERROR,
            message="Database operation failed",
            details={'operation': operation, 'error': error_code}
        )


def handle_oauth_error(error: Exception, provider: str) -> APIError:
    """
    Convert OAuth error to APIError.
    
    Args:
        error: OAuth exception
        provider: OAuth provider name
        
    Returns:
        APIError with appropriate code and message
    """
    if isinstance(error, OAuthError):
        return APIError(
            code=ErrorCodes.OAUTH_FAILED,
            message=f"Authentication with {provider} failed: {str(error)}",
            details={'provider': provider}
        )
    else:
        return APIError(
            code=ErrorCodes.OAUTH_FAILED,
            message=f"Authentication with {provider} failed",
            details={'provider': provider, 'error': str(error)}
        )


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    exceptions: tuple = (ClientError,)
) -> Callable[[F], F]:
    """
    Decorator to retry function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
        
    Example:
        @retry_with_backoff(max_retries=3)
        def my_function():
            # Function that might fail transiently
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # Check if it's a retryable error
                    if isinstance(e, ClientError):
                        error_code = e.response['Error']['Code']
                        if error_code not in [
                            'ProvisionedThroughputExceededException',
                            'RequestLimitExceeded',
                            'ThrottlingException'
                        ]:
                            # Not a retryable error, raise immediately
                            raise
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        # Last attempt failed, raise the exception
                        raise last_exception
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            return None
        
        return cast(F, wrapper)
    
    return decorator


def create_api_error_response(error: APIError, request_id: str = "") -> dict:
    """
    Create standardized API error response.
    
    Args:
        error: APIError object
        request_id: Request ID for tracing
        
    Returns:
        Error response dictionary
    """
    response = {
        'success': False,
        'error': {
            'code': error.code,
            'message': error.message
        }
    }
    
    if error.details:
        response['error']['details'] = error.details
    
    if request_id:
        response['request_id'] = request_id
    
    return response


def get_http_status_code(error_code: str) -> int:
    """
    Map error code to HTTP status code.
    
    Args:
        error_code: Error code constant
        
    Returns:
        HTTP status code
    """
    status_map = {
        ErrorCodes.INVALID_PROVIDER: 400,
        ErrorCodes.VALIDATION_ERROR: 400,
        ErrorCodes.ACCOUNT_EXISTS: 409,
        ErrorCodes.USER_NOT_FOUND: 401,
        ErrorCodes.INVALID_TOKEN: 401,
        ErrorCodes.EXPIRED_TOKEN: 401,
        ErrorCodes.METADATA_MISMATCH: 401,
        ErrorCodes.OAUTH_FAILED: 401,
        ErrorCodes.RATE_LIMIT_EXCEEDED: 429,
        ErrorCodes.SERVER_ERROR: 500,
    }
    
    return status_map.get(error_code, 500)
