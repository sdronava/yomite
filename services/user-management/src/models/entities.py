"""Core data models for user registration service."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class UserAccount:
    """User account record in DynamoDB."""
    
    user_id: str  # UUID
    email: str
    created_at: int  # Unix timestamp
    updated_at: int  # Unix timestamp
    data: Dict[str, Any] = field(default_factory=dict)  # Flexible JSON data
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        return {
            'PK': f'USER#{self.user_id}',
            'SK': 'METADATA',
            'EntityType': 'USER',
            'UserId': self.user_id,
            'Email': self.email,
            'CreatedAt': self.created_at,
            'UpdatedAt': self.updated_at,
            'Data': self.data
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'UserAccount':
        """Create from DynamoDB item."""
        return cls(
            user_id=item['UserId'],
            email=item['Email'],
            created_at=item['CreatedAt'],
            updated_at=item['UpdatedAt'],
            data=item.get('Data', {})
        )


@dataclass
class SocialIdentity:
    """Social provider identity linked to user account."""
    
    user_id: str
    provider: str  # google, facebook, github
    provider_user_id: str
    email: str
    linked_at: int  # Unix timestamp
    data: Dict[str, Any] = field(default_factory=dict)  # Profile data from provider
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        return {
            'PK': f'USER#{self.user_id}',
            'SK': f'SOCIAL#{self.provider}',
            'EntityType': 'SOCIAL_IDENTITY',
            'UserId': self.user_id,
            'Provider': self.provider,
            'ProviderUserId': self.provider_user_id,
            'Email': self.email,
            'EmailProviderKey': f'{self.email}#{self.provider}',
            'LinkedAt': self.linked_at,
            'Data': self.data
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'SocialIdentity':
        """Create from DynamoDB item."""
        return cls(
            user_id=item['UserId'],
            provider=item['Provider'],
            provider_user_id=item['ProviderUserId'],
            email=item['Email'],
            linked_at=item['LinkedAt'],
            data=item.get('Data', {})
        )


@dataclass
class Session:
    """Session record with TTL."""
    
    token: str
    user_id: str
    created_at: int
    expires_at: int  # TTL attribute
    client_ip: str
    user_agent: str
    rotation_count: int = 0
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        import hashlib
        token_hash = hashlib.sha256(self.token.encode()).hexdigest()
        
        return {
            'PK': f'SESSION#{token_hash}',
            'SK': 'METADATA',
            'EntityType': 'SESSION',
            'UserId': self.user_id,
            'SessionToken': self.token,
            'CreatedAt': self.created_at,
            'ExpiresAt': self.expires_at,
            'ClientIP': self.client_ip,
            'UserAgent': self.user_agent,
            'RotationCount': self.rotation_count
        }
    
    def to_user_session_index_item(self) -> Dict[str, Any]:
        """Convert to user session index item for listing."""
        import hashlib
        token_hash = hashlib.sha256(self.token.encode()).hexdigest()
        
        return {
            'PK': f'USER#{self.user_id}',
            'SK': f'SESSION#{token_hash}',
            'EntityType': 'SESSION_INDEX',
            'SessionToken': self.token,
            'CreatedAt': self.created_at,
            'ExpiresAt': self.expires_at
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'Session':
        """Create from DynamoDB item."""
        return cls(
            token=item['SessionToken'],
            user_id=item['UserId'],
            created_at=item['CreatedAt'],
            expires_at=item['ExpiresAt'],
            client_ip=item['ClientIP'],
            user_agent=item['UserAgent'],
            rotation_count=item.get('RotationCount', 0)
        )


@dataclass
class ClientMetadata:
    """Client information for session binding."""
    
    ip_address: str
    user_agent: str


@dataclass
class RegistrationResult:
    """Result of registration operation."""
    
    user_id: str
    email: str
    linked: bool  # True if account was linked to existing user
    message: Optional[str] = None


@dataclass
class AuthenticationResult:
    """Result of authentication operation."""
    
    session_token: str
    user_id: str
    expires_at: datetime


@dataclass
class SessionValidation:
    """Result of session validation."""
    
    valid: bool
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    requires_reauth: bool = False


@dataclass
class OAuthToken:
    """OAuth access token from provider."""
    
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None


@dataclass
class UserProfile:
    """User profile from social provider."""
    
    provider: str
    provider_user_id: str
    email: str
    name: Optional[str] = None
    picture_url: Optional[str] = None


@dataclass
class APIResponse:
    """Standard API response wrapper."""
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional['APIError'] = None
    request_id: str = ""


@dataclass
class APIError:
    """Standard error response."""
    
    code: str  # ERROR_CODE_CONSTANT
    message: str
    details: Optional[Dict[str, Any]] = None
