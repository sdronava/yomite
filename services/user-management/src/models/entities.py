"""Core data models for user registration service with Cognito."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class CognitoUserContext:
    """User context from Cognito JWT token (extracted by API Gateway)."""

    sub: str  # Cognito user ID (UUID)
    email: str
    email_verified: bool
    name: Optional[str] = None
    picture: Optional[str] = None
    identities: Optional[list] = None  # Social provider identities

    @classmethod
    def from_authorizer_claims(cls, claims: Dict[str, Any]) -> "CognitoUserContext":
        """
        Create from API Gateway authorizer claims.

        Args:
            claims: JWT claims from event['requestContext']['authorizer']['jwt']['claims']

        Returns:
            CognitoUserContext instance
        """
        return cls(
            sub=claims["sub"],
            email=claims.get("email", ""),
            email_verified=claims.get("email_verified", "false") == "true",
            name=claims.get("name"),
            picture=claims.get("picture"),
            identities=claims.get("identities"),
        )


@dataclass
class UserProfile:
    """User profile data stored in DynamoDB."""

    user_id: str  # Cognito sub
    email: str
    name: Optional[str] = None
    picture_url: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: int = 0  # Unix timestamp
    updated_at: int = 0  # Unix timestamp

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        return {
            "PK": f"USER#{self.user_id}",
            "SK": "PROFILE",
            "EntityType": "USER_PROFILE",
            "UserId": self.user_id,
            "Email": self.email,
            "Name": self.name,
            "PictureUrl": self.picture_url,
            "Preferences": self.preferences,
            "CreatedAt": self.created_at,
            "UpdatedAt": self.updated_at,
        }

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> "UserProfile":
        """Create from DynamoDB item."""
        return cls(
            user_id=item["UserId"],
            email=item["Email"],
            name=item.get("Name"),
            picture_url=item.get("PictureUrl"),
            preferences=item.get("Preferences", {}),
            created_at=item.get("CreatedAt", 0),
            updated_at=item.get("UpdatedAt", 0),
        )


@dataclass
class ClientMetadata:
    """Client information for logging and analytics."""

    ip_address: str
    user_agent: str


@dataclass
class APIResponse:
    """Standard API response wrapper."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional["APIError"] = None
    request_id: str = ""


@dataclass
class APIError:
    """Standard error response."""

    code: str  # ERROR_CODE_CONSTANT
    message: str
    details: Optional[Dict[str, Any]] = None
