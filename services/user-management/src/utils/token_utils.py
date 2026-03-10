"""Session token generation and hashing utilities."""

import secrets
import hashlib


def generate_session_token() -> str:
    """
    Generate cryptographically secure session token with 256-bit entropy.
    
    Returns:
        Session token in format: v1.{random_string}
        
    Example:
        v1.Kx7jP9mN2qR5tY8wZ3vB6nM4kL1hG0fD
    """
    # Generate 32 bytes (256 bits) of random data
    random_bytes = secrets.token_urlsafe(32)
    
    # Add version prefix for future token format changes
    return f"v1.{random_bytes}"


def hash_token(token: str) -> str:
    """
    Hash token using SHA-256 for storage in DynamoDB.
    
    Args:
        token: Session token to hash
        
    Returns:
        SHA-256 hash of the token (hex string)
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_entropy(token: str) -> bool:
    """
    Verify token has sufficient entropy (for testing).
    
    Args:
        token: Token to verify
        
    Returns:
        True if token appears to have sufficient entropy
    """
    if not token.startswith('v1.'):
        return False
    
    # Extract the random part
    random_part = token[3:]
    
    # Should be at least 32 characters (base64url encoded 32 bytes)
    if len(random_part) < 32:
        return False
    
    # Check for variety of characters (basic entropy check)
    unique_chars = len(set(random_part))
    if unique_chars < 10:  # Should have good character variety
        return False
    
    return True
