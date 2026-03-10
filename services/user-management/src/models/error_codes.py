"""Standard error codes for API responses."""


class ErrorCodes:
    """Error code constants."""
    
    # OAuth errors
    INVALID_PROVIDER = "INVALID_PROVIDER"
    OAUTH_FAILED = "OAUTH_FAILED"
    
    # Registration errors
    ACCOUNT_EXISTS = "ACCOUNT_EXISTS"
    
    # Authentication errors
    USER_NOT_FOUND = "USER_NOT_FOUND"
    
    # Session errors
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    METADATA_MISMATCH = "METADATA_MISMATCH"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Server errors
    SERVER_ERROR = "SERVER_ERROR"
