# Design Document: User Registration Service

## Overview

The User Registration Service provides secure user identity management for the Yomite application through social login integration. This service handles user registration, authentication, session management, and account linking across multiple social providers.

### Goals

- Enable frictionless user onboarding through social login providers
- Provide secure session management with token-based authentication
- Support account linking for users with multiple social identities
- Maintain security best practices including rate limiting, encryption, and HTTPS enforcement
- Enable local development with production-like behavior
- Design for cloud-agnostic deployment with AWS implementation

### Non-Goals

- Password-based authentication (social login only)
- Multi-factor authentication (future enhancement)
- User profile management beyond basic identity (separate service)
- Email verification workflows (delegated to social providers)

## Architecture

### High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        FC[Frontend Client<br/>React/Vue/TypeScript]
    end
    
    subgraph "API Layer"
        AG[API Gateway<br/>HTTPS/Rate Limiting]
    end
    
    subgraph "Service Layer"
        RS[Registration Service<br/>Python]
        AS[Authentication Service<br/>Python]
        SM[Session Manager<br/>Python]
    end
    
    subgraph "External Services"
        SP1[Google OAuth]
        SP2[Facebook OAuth]
        SP3[GitHub OAuth]
    end
    
    subgraph "Data Layer"
        DB[(User Database<br/>PostgreSQL)]
        SS[(Session Store<br/>Redis)]
    end
    
    FC -->|HTTPS| AG
    AG --> RS
    AG --> AS
    AG --> SM
    
    RS -->|OAuth Flow| SP1
    RS -->|OAuth Flow| SP2
    RS -->|OAuth Flow| SP3
    
    AS -->|OAuth Flow| SP1
    AS -->|OAuth Flow| SP2
    AS -->|OAuth Flow| SP3
    
    RS -->|Store User| DB
    AS -->|Query User| DB
    SM -->|Store/Validate| SS
    
    style FC fill:#e1f5ff
    style AG fill:#fff4e1
    style RS fill:#e8f5e9
    style AS fill:#e8f5e9
    style SM fill:#e8f5e9
    style DB fill:#f3e5f5
    style SS fill:#f3e5f5
```

### Registration Process Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API Gateway
    participant Registration Service
    participant Social Provider
    participant Database
    
    User->>Frontend: Click "Sign up with Google"
    Frontend->>API Gateway: POST /auth/register/google
    API Gateway->>Registration Service: Forward request
    Registration Service->>Social Provider: Initiate OAuth flow
    Social Provider->>User: Request authorization
    User->>Social Provider: Grant permission
    Social Provider->>Registration Service: Return user credentials
    Registration Service->>Database: Check if email exists
    
    alt Email does not exist
        Registration Service->>Database: Create new user account
        Database-->>Registration Service: User created
        Registration Service->>API Gateway: Return success + user data
    else Email exists with different provider
        Registration Service->>Database: Link new provider to existing account
        Database-->>Registration Service: Account linked
        Registration Service->>API Gateway: Return success + linked notification
    else Email exists with same provider
        Registration Service->>API Gateway: Return error (account exists)
    end
    
    API Gateway->>Frontend: Return response
    Frontend->>User: Display result
```

### Login Process Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API Gateway
    participant Auth Service
    participant Social Provider
    participant Database
    participant Session Manager
    participant Session Store
    
    User->>Frontend: Click "Login with Google"
    Frontend->>API Gateway: POST /auth/login/google
    API Gateway->>Auth Service: Forward request
    Auth Service->>Social Provider: Initiate OAuth flow
    Social Provider->>User: Request authorization
    User->>Social Provider: Grant permission
    Social Provider->>Auth Service: Return user credentials
    Auth Service->>Database: Query user by email + provider
    
    alt User account exists
        Database-->>Auth Service: Return user account
        Auth Service->>Session Manager: Create session
        Session Manager->>Session Store: Store session with metadata
        Session Store-->>Session Manager: Session created
        Session Manager-->>Auth Service: Return session token
        Auth Service->>API Gateway: Return success + token
    else User account does not exist
        Auth Service->>API Gateway: Return error (no account)
    end
    
    API Gateway->>Frontend: Return response
    Frontend->>User: Display result / redirect to app
```

### Component Architecture

```mermaid
graph TB
    subgraph "Registration Service"
        RC[Registration Controller]
        OC[OAuth Client Manager]
        AL[Account Linker]
        UV[User Validator]
    end
    
    subgraph "Authentication Service"
        AC[Auth Controller]
        OA[OAuth Authenticator]
        TV[Token Validator]
    end
    
    subgraph "Session Manager"
        SC[Session Controller]
        TG[Token Generator]
        SV[Session Validator]
        TR[Token Rotator]
    end
    
    subgraph "Shared Components"
        RL[Rate Limiter]
        LOG[Logger]
        ERR[Error Handler]
    end
    
    RC --> OC
    RC --> AL
    RC --> UV
    RC --> RL
    RC --> LOG
    RC --> ERR
    
    AC --> OA
    AC --> TV
    AC --> RL
    AC --> LOG
    AC --> ERR
    
    SC --> TG
    SC --> SV
    SC --> TR
    SC --> LOG
    SC --> ERR
    
    style RC fill:#a5d6a7
    style AC fill:#a5d6a7
    style SC fill:#a5d6a7
    style RL fill:#ffcc80
    style LOG fill:#ffcc80
    style ERR fill:#ffcc80
```

## Components and Interfaces

### API Gateway

**Responsibilities:**
- Route requests to appropriate services
- Enforce HTTPS for all endpoints
- Apply rate limiting policies
- Add request tracing identifiers
- Handle CORS for frontend clients

**Endpoints:**

```
POST /auth/register/{provider}
  Request: { redirect_uri: string }
  Response: { user_id: string, email: string, linked: boolean, message?: string }
  Errors: 400 (invalid provider), 409 (account exists), 500 (server error)

POST /auth/login/{provider}
  Request: { redirect_uri: string }
  Response: { session_token: string, user_id: string, expires_at: timestamp }
  Errors: 400 (invalid provider), 401 (no account), 500 (server error)

POST /auth/logout
  Request: { session_token: string }
  Response: { success: boolean }
  Errors: 401 (invalid token), 500 (server error)

GET /auth/validate
  Request: Headers { Authorization: Bearer <session_token> }
  Response: { valid: boolean, user_id: string, expires_at: timestamp }
  Errors: 401 (invalid/expired token), 500 (server error)
```

### Registration Service

**Responsibilities:**
- Orchestrate OAuth flows with social providers
- Create new user accounts
- Handle duplicate email scenarios with account linking
- Validate user input data
- Prevent injection attacks

**Interface:**

```python
class RegistrationService:
    def register_with_provider(
        self, 
        provider: str, 
        oauth_code: str,
        redirect_uri: str
    ) -> RegistrationResult:
        """
        Register a new user or link account with social provider.
        
        Args:
            provider: Social provider name (google, facebook, github)
            oauth_code: Authorization code from OAuth flow
            redirect_uri: Redirect URI for OAuth callback
            
        Returns:
            RegistrationResult with user_id, email, and linked status
            
        Raises:
            InvalidProviderError: Provider not supported
            OAuthError: OAuth flow failed
            AccountExistsError: Account already exists with same provider
        """
        pass
    
    def get_supported_providers(self) -> List[str]:
        """Return list of supported social providers."""
        pass
```

**Data Models:**

```python
@dataclass
class RegistrationResult:
    user_id: str
    email: str
    linked: bool  # True if account was linked to existing user
    message: Optional[str] = None
```

### Authentication Service

**Responsibilities:**
- Verify user identity through social providers
- Query existing user accounts
- Coordinate with Session Manager for token creation
- Log authentication attempts

**Interface:**

```python
class AuthenticationService:
    def authenticate_with_provider(
        self,
        provider: str,
        oauth_code: str,
        redirect_uri: str,
        client_metadata: ClientMetadata
    ) -> AuthenticationResult:
        """
        Authenticate user with social provider and create session.
        
        Args:
            provider: Social provider name
            oauth_code: Authorization code from OAuth flow
            redirect_uri: Redirect URI for OAuth callback
            client_metadata: IP address and user agent for session binding
            
        Returns:
            AuthenticationResult with session token and user info
            
        Raises:
            InvalidProviderError: Provider not supported
            OAuthError: OAuth flow failed
            UserNotFoundError: No account exists for this user
        """
        pass
```

**Data Models:**

```python
@dataclass
class ClientMetadata:
    ip_address: str
    user_agent: str

@dataclass
class AuthenticationResult:
    session_token: str
    user_id: str
    expires_at: datetime
```

### Session Manager

**Responsibilities:**
- Generate cryptographically secure session tokens
- Store and validate session data
- Bind sessions to client metadata (IP, user agent)
- Rotate tokens during active sessions
- Invalidate sessions on logout
- Enforce session expiration

**Interface:**

```python
class SessionManager:
    def create_session(
        self,
        user_id: str,
        client_metadata: ClientMetadata
    ) -> Session:
        """
        Create a new session with secure token.
        
        Args:
            user_id: User identifier
            client_metadata: Client IP and user agent for binding
            
        Returns:
            Session with token and expiration
        """
        pass
    
    def validate_session(
        self,
        session_token: str,
        client_metadata: ClientMetadata
    ) -> SessionValidation:
        """
        Validate session token and check client metadata.
        
        Args:
            session_token: Token to validate
            client_metadata: Current client IP and user agent
            
        Returns:
            SessionValidation with validity status and user_id
            
        Raises:
            InvalidTokenError: Token is invalid or expired
            MetadataMismatchError: Client metadata doesn't match
        """
        pass
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session token."""
        pass
    
    def rotate_token(
        self,
        old_token: str,
        client_metadata: ClientMetadata
    ) -> Session:
        """
        Rotate session token while maintaining session.
        
        Args:
            old_token: Current session token
            client_metadata: Client metadata for validation
            
        Returns:
            New Session with rotated token
        """
        pass
```

**Data Models:**

```python
@dataclass
class Session:
    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    client_ip: str
    user_agent: str

@dataclass
class SessionValidation:
    valid: bool
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    requires_reauth: bool = False
```

### OAuth Client Manager

**Responsibilities:**
- Manage OAuth client configurations for each provider
- Execute OAuth authorization code flow
- Exchange authorization codes for access tokens
- Retrieve user profile information from providers

**Interface:**

```python
class OAuthClientManager:
    def get_authorization_url(
        self,
        provider: str,
        redirect_uri: str,
        state: str
    ) -> str:
        """Generate OAuth authorization URL."""
        pass
    
    def exchange_code_for_token(
        self,
        provider: str,
        code: str,
        redirect_uri: str
    ) -> OAuthToken:
        """Exchange authorization code for access token."""
        pass
    
    def get_user_profile(
        self,
        provider: str,
        access_token: str
    ) -> UserProfile:
        """Retrieve user profile from provider."""
        pass
```

**Data Models:**

```python
@dataclass
class OAuthToken:
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None

@dataclass
class UserProfile:
    provider: str
    provider_user_id: str
    email: str
    name: Optional[str] = None
    picture_url: Optional[str] = None
```

## Data Models

### User Account Schema

```python
@dataclass
class UserAccount:
    """Persistent user account record."""
    user_id: str  # UUID primary key
    email: str  # Unique, indexed
    created_at: datetime
    updated_at: datetime
    social_identities: List[SocialIdentity]

@dataclass
class SocialIdentity:
    """Social provider identity linked to user account."""
    provider: str  # google, facebook, github
    provider_user_id: str  # User ID from provider
    linked_at: datetime
```

**Database Schema (PostgreSQL):**

```sql
CREATE TABLE user_accounts (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_user_email ON user_accounts(email);

CREATE TABLE social_identities (
    identity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_accounts(user_id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    linked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

CREATE INDEX idx_social_identity_lookup ON social_identities(provider, provider_user_id);
CREATE INDEX idx_user_identities ON social_identities(user_id);
```

### Session Data Schema

**Session Store (Redis):**

```
Key: session:{token_hash}
Value: {
    "user_id": "uuid",
    "created_at": "timestamp",
    "expires_at": "timestamp",
    "client_ip": "ip_address",
    "user_agent": "user_agent_string",
    "rotation_count": integer
}
TTL: 24 hours (auto-expire)
```

**Token Format:**
- 256-bit random value encoded as base64url
- Example: `v1.Kx7jP9mN2qR5tY8wZ3vB6nM4kL1hG0fD`
- Prefix `v1.` for versioning

### API Response Models

```python
@dataclass
class APIResponse:
    """Standard API response wrapper."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[APIError] = None
    request_id: str = ""

@dataclass
class APIError:
    """Standard error response."""
    code: str  # ERROR_CODE_CONSTANT
    message: str
    details: Optional[Dict] = None
```

**Error Codes:**
- `INVALID_PROVIDER`: Unsupported social provider
- `OAUTH_FAILED`: OAuth flow failed
- `ACCOUNT_EXISTS`: Account already exists with same provider
- `USER_NOT_FOUND`: No account exists for user
- `INVALID_TOKEN`: Session token is invalid
- `EXPIRED_TOKEN`: Session token has expired
- `METADATA_MISMATCH`: Client metadata doesn't match session
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `VALIDATION_ERROR`: Input validation failed
- `SERVER_ERROR`: Internal server error


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified several areas where properties can be consolidated to eliminate redundancy:

**Consolidations Made:**
1. OAuth flow initiation (1.1, 3.1) - Combined into single property covering both registration and login
2. Account persistence round-trips (1.5, 11.1) - Combined into single property about data persistence
3. Session persistence round-trips (11.2) - Covered by session validation properties
4. Error response format (12.3, 12.4) - Combined into single property about error status codes
5. Logging properties (8.2, 8.3, 8.4) - Combined into single property about operation logging
6. Token validation (4.2, 4.3, 4.4) - Combined into comprehensive validation property

### Property 1: OAuth Flow Initiation

*For any* supported social provider and any registration or login request, the service SHALL initiate the OAuth authorization flow with that provider.

**Validates: Requirements 1.1, 3.1**

### Property 2: Account Creation from Valid Credentials

*For any* valid user credentials returned from a social provider, if no account exists with that email, the Registration Service SHALL create a new User_Account containing the provider identifier and email address.

**Validates: Requirements 1.2, 1.5**

### Property 3: Provider Error Propagation

*For any* error returned by a social provider during OAuth flow, the service SHALL return a descriptive error message to the client that includes the error type.

**Validates: Requirements 1.3**

### Property 4: Account Linking for Duplicate Emails

*For any* registration attempt where the email matches an existing account but the provider is different, the Registration Service SHALL link the new provider to the existing account rather than creating a duplicate account.

**Validates: Requirements 2.1**

### Property 5: Account Linking Notification

*For any* account linking operation, the Registration Service SHALL include a notification in the response indicating that accounts have been linked.

**Validates: Requirements 2.2**

### Property 6: Duplicate Provider Registration Error

*For any* registration attempt where both the email and provider match an existing account, the Registration Service SHALL return an error indicating the account already exists.

**Validates: Requirements 2.3**

### Property 7: Account Persistence Round-Trip

*For any* user account created through registration, querying the database by email SHALL return an account with the same email and provider identifier.

**Validates: Requirements 1.5, 11.1**

### Property 8: Session Creation on Successful Authentication

*For any* valid authentication with credentials matching an existing account, the Authentication Service SHALL create a session token and return it to the client.

**Validates: Requirements 3.2, 3.4**

### Property 9: Authentication Error for Non-Existent Accounts

*For any* valid credentials from a social provider that do not match any existing account, the Authentication Service SHALL return an error indicating no account exists.

**Validates: Requirements 3.3**

### Property 10: Session Token Entropy

*For any* generated session token, the token SHALL contain at least 256 bits of entropy and SHALL be unique across all generated tokens.

**Validates: Requirements 3.5, 7.1**

### Property 11: Session Expiration Configuration

*For any* created session, the session SHALL have an expiration time that is configurable and does not exceed 24 hours from creation.

**Validates: Requirements 4.1, 7.5**

### Property 12: Session Validation

*For any* session token and client metadata, validation SHALL succeed if and only if the token is valid, not expired, and the client metadata matches the session's stored metadata.

**Validates: Requirements 4.2, 4.3, 4.4, 7.3**

### Property 13: Session Invalidation on Logout

*For any* valid session token, after logout is called, subsequent validation attempts with that token SHALL fail.

**Validates: Requirements 5.1, 5.2**

### Property 14: Logout Confirmation

*For any* successful logout operation, the service SHALL return a success confirmation to the client.

**Validates: Requirements 5.3**

### Property 15: Rate Limiting Enforcement

*For any* client making requests to authentication endpoints, after exceeding the configured rate limit threshold, subsequent requests SHALL be rejected with a rate limit error until the time window resets.

**Validates: Requirements 6.3, 6.4**

### Property 16: Input Validation

*For any* input data containing SQL injection patterns, script tags, or other malicious content, the service SHALL reject the input and return a validation error.

**Validates: Requirements 6.5**

### Property 17: Session Metadata Binding

*For any* created session, the session data SHALL include the client IP address and user agent provided during authentication.

**Validates: Requirements 7.2**

### Property 18: Token Rotation

*For any* valid session token, calling the rotation function SHALL return a new token that validates successfully while the old token becomes invalid.

**Validates: Requirements 7.4**

### Property 19: Operation Logging

*For any* registration attempt, authentication attempt, session creation, session validation failure, or logout event, the service SHALL create a log entry with timestamp, operation type, and success/failure status.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Property 20: Sensitive Data Exclusion from Logs

*For any* log entry created by the system, the log SHALL NOT contain session tokens, OAuth access tokens, or complete social provider credentials.

**Validates: Requirements 8.5**

### Property 21: Database Constraint Enforcement

*For any* attempt to create a user account with an email that already exists in the database, the database SHALL reject the operation with a constraint violation error.

**Validates: Requirements 11.5**

### Property 22: Database Error Handling

*For any* transient database error (connection timeout, deadlock), the service SHALL retry the operation according to configured retry policy and return an appropriate error if all retries fail.

**Validates: Requirements 11.3**

### Property 23: JSON Response Format

*For any* API response, the response body SHALL be valid JSON that can be parsed without errors.

**Validates: Requirements 12.1**

### Property 24: Success Status Codes

*For any* successful API operation, the response SHALL have a status code in the 2xx range.

**Validates: Requirements 12.2**

### Property 25: Error Status Codes

*For any* failed API operation, the response SHALL have a status code in the 4xx range for client errors or 5xx range for server errors.

**Validates: Requirements 12.3, 12.4**

### Property 26: Request Tracing

*For any* API response, the response SHALL include a unique request identifier that can be used for tracing and debugging.

**Validates: Requirements 12.5**

## Error Handling

### Error Categories

**Client Errors (4xx):**
- `400 Bad Request`: Invalid input data, malformed requests
- `401 Unauthorized`: Invalid or expired session token, authentication failed
- `409 Conflict`: Account already exists with same provider
- `429 Too Many Requests`: Rate limit exceeded

**Server Errors (5xx):**
- `500 Internal Server Error`: Unexpected server errors
- `502 Bad Gateway`: Social provider unavailable
- `503 Service Unavailable`: Database or session store unavailable
- `504 Gateway Timeout`: Social provider timeout

### Error Response Format

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "additional context"
    }
  },
  "request_id": "uuid"
}
```

### Error Handling Strategies

**OAuth Errors:**
- Capture provider-specific error codes
- Map to standardized error messages
- Log full error details for debugging
- Return user-friendly messages to client

**Database Errors:**
- Distinguish transient from permanent errors
- Retry transient errors with exponential backoff
- Maximum 3 retry attempts
- Return generic error to client, log details

**Session Errors:**
- Clear distinction between expired and invalid tokens
- Prompt re-authentication for expired sessions
- Reject invalid tokens immediately
- Log suspicious validation patterns

**Rate Limiting:**
- Track requests per client IP
- Sliding window algorithm
- Return `Retry-After` header
- Temporarily block after threshold

**Input Validation:**
- Validate all inputs before processing
- Sanitize data to prevent injection
- Return specific validation errors
- Log validation failures for security monitoring

### Retry Logic

**Transient Errors:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(TransientError)
)
def operation_with_retry():
    pass
```

**Circuit Breaker:**
- Open circuit after 5 consecutive failures
- Half-open state after 30 seconds
- Close circuit after 2 successful requests

## Testing Strategy

### Dual Testing Approach

The User Registration Service requires both unit testing and property-based testing to ensure comprehensive correctness validation:

**Unit Tests:**
- Specific examples demonstrating correct behavior
- Edge cases (empty inputs, boundary conditions)
- Error conditions and exception handling
- Integration points between components
- Mock external dependencies (social providers, databases)

**Property-Based Tests:**
- Universal properties that hold for all inputs
- Comprehensive input coverage through randomization
- Minimum 100 iterations per property test
- Each test references its design document property
- Tag format: `Feature: user-registration-service, Property {number}: {property_text}`

### Property-Based Testing Framework

**Python Framework:** Hypothesis (https://hypothesis.readthedocs.io/)

**Configuration:**
```python
from hypothesis import given, settings, strategies as st

@settings(max_examples=100)
@given(
    email=st.emails(),
    provider=st.sampled_from(['google', 'facebook', 'github'])
)
def test_property_X(email, provider):
    """
    Feature: user-registration-service
    Property 2: Account Creation from Valid Credentials
    
    For any valid user credentials returned from a social provider,
    if no account exists with that email, the Registration Service
    SHALL create a new User_Account containing the provider identifier
    and email address.
    """
    # Test implementation
    pass
```

### Test Organization

```
tests/
├── unit/
│   ├── test_registration_service.py
│   ├── test_authentication_service.py
│   ├── test_session_manager.py
│   └── test_oauth_client.py
├── property/
│   ├── test_registration_properties.py
│   ├── test_authentication_properties.py
│   ├── test_session_properties.py
│   └── test_api_properties.py
├── integration/
│   ├── test_registration_flow.py
│   ├── test_authentication_flow.py
│   └── test_account_linking.py
└── fixtures/
    ├── mock_providers.py
    └── test_data.py
```

### Test Coverage Requirements

**Minimum Coverage:**
- Unit tests: 80% code coverage
- Property tests: All 26 correctness properties implemented
- Integration tests: All critical user flows

**Critical Paths:**
- Complete registration flow (new user)
- Complete registration flow (account linking)
- Complete authentication flow
- Session validation and expiration
- Logout and token invalidation
- Rate limiting enforcement
- Error handling for all error types

### Mock Social Providers

For local testing and CI/CD:

```python
class MockOAuthProvider:
    """Mock social provider for testing."""
    
    def authorize(self, redirect_uri: str) -> str:
        """Return mock authorization URL."""
        pass
    
    def exchange_code(self, code: str) -> OAuthToken:
        """Return mock access token."""
        pass
    
    def get_profile(self, token: str) -> UserProfile:
        """Return mock user profile."""
        pass
    
    def simulate_error(self, error_type: str):
        """Simulate provider errors for testing."""
        pass
```

### Test Data Generators

**Hypothesis Strategies:**
```python
# Email addresses
emails = st.emails()

# Social providers
providers = st.sampled_from(['google', 'facebook', 'github'])

# User profiles
user_profiles = st.builds(
    UserProfile,
    provider=providers,
    provider_user_id=st.text(min_size=1, max_size=50),
    email=emails,
    name=st.text(min_size=1, max_size=100),
    picture_url=st.one_of(st.none(), st.from_regex(r'https://.*'))
)

# Session tokens
session_tokens = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=43,
    max_size=43
)

# Client metadata
client_metadata = st.builds(
    ClientMetadata,
    ip_address=st.ip_addresses(v=4).map(str),
    user_agent=st.text(min_size=10, max_size=200)
)
```

### Performance Testing

While not part of correctness properties, performance benchmarks should be established:

**Targets:**
- Registration: < 2 seconds (including OAuth round-trip)
- Authentication: < 1.5 seconds (including OAuth round-trip)
- Session validation: < 50ms
- Token rotation: < 100ms
- Database queries: < 100ms (p95)

### Security Testing

**Automated Security Tests:**
- SQL injection attempts (covered by Property 16)
- XSS attempts (covered by Property 16)
- Session hijacking attempts (covered by Property 12)
- Rate limit bypass attempts (covered by Property 15)
- Token prediction attempts (covered by Property 10)

**Manual Security Review:**
- OAuth implementation review
- Token generation review
- Session management review
- Infrastructure security review

### Continuous Integration

**CI Pipeline:**
1. Lint and format checks
2. Unit tests (parallel execution)
3. Property-based tests (parallel execution)
4. Integration tests (sequential)
5. Security scans
6. Coverage report generation
7. Build Docker images
8. Deploy to staging (on main branch)

**Test Execution Time Targets:**
- Unit tests: < 2 minutes
- Property tests: < 5 minutes (100 iterations each)
- Integration tests: < 3 minutes
- Total CI time: < 15 minutes


## Deployment Architecture

### Container Architecture

```mermaid
graph TB
    subgraph "Container Orchestration (ECS/Kubernetes)"
        subgraph "API Gateway Container"
            AG[Nginx/API Gateway]
        end
        
        subgraph "Application Containers"
            RS1[Registration Service]
            RS2[Registration Service]
            AS1[Auth Service]
            AS2[Auth Service]
            SM1[Session Manager]
            SM2[Session Manager]
        end
    end
    
    subgraph "Data Services"
        DB[(PostgreSQL RDS)]
        CACHE[(Redis ElastiCache)]
    end
    
    subgraph "External"
        SP[Social Providers]
    end
    
    AG --> RS1
    AG --> RS2
    AG --> AS1
    AG --> AS2
    AG --> SM1
    AG --> SM2
    
    RS1 --> DB
    RS2 --> DB
    AS1 --> DB
    AS2 --> DB
    SM1 --> CACHE
    SM2 --> CACHE
    
    RS1 --> SP
    RS2 --> SP
    AS1 --> SP
    AS2 --> SP
    
    style AG fill:#fff4e1
    style DB fill:#f3e5f5
    style CACHE fill:#f3e5f5
```

### Infrastructure Components

**Compute:**
- ECS Fargate or EKS for container orchestration
- Auto-scaling based on CPU/memory utilization
- Minimum 2 instances per service for high availability
- Health checks on `/health` endpoint

**Database:**
- Amazon RDS PostgreSQL (Multi-AZ)
- Automated backups with 7-day retention
- Read replicas for scaling (future)
- Connection pooling via PgBouncer

**Session Store:**
- Amazon ElastiCache Redis (Cluster mode)
- Automatic failover
- Encryption at rest and in transit
- TTL-based expiration

**Networking:**
- VPC with public and private subnets
- Application Load Balancer for traffic distribution
- Security groups restricting access
- NAT Gateway for outbound traffic from private subnets

**Secrets Management:**
- AWS Secrets Manager for OAuth credentials
- IAM roles for service authentication
- Automatic secret rotation
- Encryption at rest

### Environment Configuration

**Development:**
- Single container instance per service
- Local PostgreSQL in Docker
- Local Redis in Docker
- Mock OAuth providers
- Relaxed rate limits

**Staging:**
- 2 container instances per service
- RDS PostgreSQL (smaller instance)
- ElastiCache Redis (smaller instance)
- Real OAuth providers (test apps)
- Production-like rate limits

**Production:**
- 3+ container instances per service (auto-scaled)
- RDS PostgreSQL (Multi-AZ, production size)
- ElastiCache Redis (Cluster mode)
- Real OAuth providers (production apps)
- Strict rate limits and monitoring

### Infrastructure as Code

**AWS CDK Structure:**

```
infrastructure/
├── bin/
│   └── app.ts                 # CDK app entry point
├── lib/
│   ├── stacks/
│   │   ├── network-stack.ts   # VPC, subnets, security groups
│   │   ├── database-stack.ts  # RDS PostgreSQL
│   │   ├── cache-stack.ts     # ElastiCache Redis
│   │   ├── compute-stack.ts   # ECS/EKS cluster
│   │   └── service-stack.ts   # Service definitions
│   ├── constructs/
│   │   ├── service.ts         # Reusable service construct
│   │   └── monitoring.ts      # CloudWatch alarms
│   └── config/
│       ├── dev.ts             # Development config
│       ├── staging.ts         # Staging config
│       └── prod.ts            # Production config
├── cdk.json
└── package.json
```

**Key CDK Constructs:**

```typescript
// Service construct example
export class UserRegistrationService extends Construct {
  constructor(scope: Construct, id: string, props: ServiceProps) {
    super(scope, id);
    
    // Task definition
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDef', {
      memoryLimitMiB: 512,
      cpu: 256,
    });
    
    // Container
    taskDefinition.addContainer('app', {
      image: ecs.ContainerImage.fromRegistry(props.imageUri),
      environment: {
        DATABASE_URL: props.databaseUrl,
        REDIS_URL: props.redisUrl,
        ENVIRONMENT: props.environment,
      },
      secrets: {
        GOOGLE_CLIENT_ID: ecs.Secret.fromSecretsManager(props.googleSecret, 'client_id'),
        GOOGLE_CLIENT_SECRET: ecs.Secret.fromSecretsManager(props.googleSecret, 'client_secret'),
        // ... other secrets
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'user-registration',
      }),
    });
    
    // Service
    new ecs.FargateService(this, 'Service', {
      cluster: props.cluster,
      taskDefinition,
      desiredCount: props.desiredCount,
      healthCheckGracePeriod: cdk.Duration.seconds(60),
    });
  }
}
```

### Local Development Setup

**Docker Compose Configuration:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: yomite_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  registration-service:
    build:
      context: ./services/user-management
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://dev:dev@postgres:5432/yomite_dev
      REDIS_URL: redis://redis:6379
      ENVIRONMENT: development
      MOCK_OAUTH: "true"
    ports:
      - "8001:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./services/user-management:/app

  api-gateway:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - registration-service

volumes:
  postgres_data:
  redis_data:
```

**Setup Commands:**

```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec registration-service python manage.py migrate

# Run tests
docker-compose exec registration-service pytest

# View logs
docker-compose logs -f registration-service

# Stop all services
docker-compose down
```

### Monitoring and Observability

**Metrics to Track:**

*Service Metrics:*
- Request rate (requests/second)
- Error rate (errors/second)
- Response time (p50, p95, p99)
- Active sessions count
- Registration success/failure rate
- Authentication success/failure rate

*Infrastructure Metrics:*
- CPU utilization
- Memory utilization
- Database connections
- Redis memory usage
- Network throughput

*Business Metrics:*
- New user registrations per day
- Active users per day
- Account linking rate
- Provider distribution (Google vs Facebook vs GitHub)

**Logging Strategy:**

*Structured Logging Format:*
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "service": "registration-service",
  "request_id": "uuid",
  "event": "user_registered",
  "user_id": "uuid",
  "provider": "google",
  "duration_ms": 1234,
  "metadata": {
    "ip_address": "1.2.3.4",
    "user_agent": "Mozilla/5.0..."
  }
}
```

*Log Levels:*
- DEBUG: Detailed diagnostic information (development only)
- INFO: General informational messages (successful operations)
- WARNING: Warning messages (rate limit approaching, slow queries)
- ERROR: Error messages (operation failures)
- CRITICAL: Critical issues (service unavailable, data corruption)

**Alerting:**

*Critical Alerts (PagerDuty):*
- Service down (health check failures)
- Error rate > 5%
- Database connection failures
- Redis connection failures
- Response time p95 > 3 seconds

*Warning Alerts (Email/Slack):*
- Error rate > 1%
- Response time p95 > 2 seconds
- CPU utilization > 80%
- Memory utilization > 80%
- Database connection pool > 80% utilized

### Security Considerations

**Network Security:**
- All traffic encrypted in transit (TLS 1.3)
- Security groups restricting access to necessary ports only
- Private subnets for application and data layers
- WAF rules for common attack patterns

**Data Security:**
- Encryption at rest for database and session store
- Secrets stored in AWS Secrets Manager
- No sensitive data in logs or error messages
- Regular security patching of dependencies

**Application Security:**
- Input validation and sanitization
- Rate limiting per IP address
- Session token rotation
- CSRF protection for state parameters
- OAuth state parameter validation

**Compliance:**
- GDPR considerations for user data
- Data retention policies
- Right to deletion support
- Audit logging for compliance

### Disaster Recovery

**Backup Strategy:**
- Automated daily database backups (7-day retention)
- Point-in-time recovery capability
- Session store data is ephemeral (no backup needed)
- Infrastructure code in version control

**Recovery Procedures:**

*Database Failure:*
1. Automatic failover to standby (Multi-AZ)
2. RTO: < 2 minutes
3. RPO: < 5 minutes

*Service Failure:*
1. Auto-scaling replaces failed instances
2. Health checks detect failures
3. RTO: < 1 minute

*Region Failure:*
1. Manual failover to backup region (future)
2. RTO: < 30 minutes
3. RPO: < 15 minutes

### Scalability Considerations

**Horizontal Scaling:**
- Stateless service design enables easy scaling
- Auto-scaling based on CPU/memory metrics
- Load balancer distributes traffic evenly
- Database read replicas for read-heavy workloads (future)

**Vertical Scaling:**
- Container resource limits adjustable
- Database instance size upgradeable
- Redis cluster size adjustable

**Performance Optimization:**
- Connection pooling for database
- Redis caching for session validation
- Async I/O for external API calls
- Batch operations where possible

**Capacity Planning:**

*Current Target:*
- 1,000 registrations per day
- 10,000 authentications per day
- 100,000 active sessions
- 50 requests per second peak

*Future Growth (12 months):*
- 10,000 registrations per day
- 100,000 authentications per day
- 1,000,000 active sessions
- 500 requests per second peak

### AWS Cost Estimates

**Detailed cost analysis available in:** `.kiro/specs/user-registration-service/cost-analysis.md`

**Monthly Cost Comparison (US East - N. Virginia, ON DEMAND pricing):**

| Configuration | Monthly Cost | Key Components |
|--------------|--------------|----------------|
| **1/10th Target** | **~$140/month** | Minimal production setup for early stage |
| **Current Target** | **~$220/month** | Full production setup for target capacity |

**Cost Breakdown by Service (Current Target):**
- AWS Fargate (ECS): $56/month (3 services × 2 instances, ARM-based)
- RDS PostgreSQL Multi-AZ: $49/month (db.t4g.small, 20GB storage)
- ElastiCache Redis: $47/month (cache.t4g.small, 2-node cluster)
- Application Load Balancer: $20/month (with minimal LCU usage)
- NAT Gateway: $33/month (with minimal data processing)
- CloudWatch + Secrets Manager + Data Transfer: $10/month

**Cost Optimization Opportunities:**
- Use ARM-based Fargate (Graviton2) for 20% savings over x86 (already included)
- Reserved Instances after 3-6 months: up to 60% savings on RDS and ElastiCache
- Savings Plans for Fargate after establishing usage: up to 50% savings
- Start with 1/10th target during development to minimize costs
- First 12 months: AWS Free Tier provides ~$50-75/month in credits

**Scaling Cost Impact:**
- 1/10th → Current Target: +57% cost increase
- Current Target → Future Growth: +150-200% cost increase (estimated)

**Note:** Costs exclude development/staging environments, CI/CD infrastructure, AWS Support plans, and domain/DNS costs.

## Design Decisions and Trade-offs

### Social Login Only

**Decision:** Support only social login providers, no password-based authentication.

**Rationale:**
- Reduces security burden (no password storage/hashing)
- Improves user experience (no password to remember)
- Leverages provider's security infrastructure
- Faster implementation

**Trade-offs:**
- Users without social accounts cannot register
- Dependency on external providers
- Provider outages affect our service

**Mitigation:**
- Support multiple providers for redundancy
- Clear error messages when providers are down
- Consider adding email/password in future if needed

### Session Token Binding

**Decision:** Bind session tokens to client IP and user agent.

**Rationale:**
- Prevents session hijacking
- Adds security layer beyond token secrecy
- Detects suspicious activity

**Trade-offs:**
- Users on mobile networks may have changing IPs
- VPN users may trigger re-authentication
- Adds complexity to validation logic

**Mitigation:**
- Allow IP changes within same subnet
- Graceful re-authentication flow
- Clear error messages for users

### Account Linking

**Decision:** Automatically link accounts with matching emails from different providers.

**Rationale:**
- Prevents duplicate accounts
- Improves user experience
- Simplifies account management

**Trade-offs:**
- Potential security risk if email is compromised
- User may not expect automatic linking
- Complexity in handling multiple providers

**Mitigation:**
- Notify user when linking occurs
- Require email verification from providers
- Allow users to unlink providers (future)

### Token Rotation

**Decision:** Implement periodic token rotation during active sessions.

**Rationale:**
- Limits window for token compromise
- Security best practice
- Reduces impact of token leakage

**Trade-offs:**
- Adds complexity to client implementation
- Potential for race conditions
- Additional database/cache operations

**Mitigation:**
- Grace period for old tokens during rotation
- Clear documentation for frontend developers
- Automatic rotation handling in SDK (future)

### Cloud-Agnostic Design

**Decision:** Design for cloud-agnostic deployment with AWS implementation.

**Rationale:**
- Flexibility to change providers
- Avoids vendor lock-in
- Portable architecture

**Trade-offs:**
- Cannot use AWS-specific features optimally
- More abstraction layers
- Potentially higher complexity

**Mitigation:**
- Use standard protocols and interfaces
- Abstract cloud-specific code into adapters
- Document AWS-specific implementations

## Future Enhancements

**Phase 2 (3-6 months):**
- Multi-factor authentication support
- Email/password authentication option
- User profile management endpoints
- Account deletion and data export (GDPR)
- Provider unlinking capability

**Phase 3 (6-12 months):**
- Additional social providers (Twitter, LinkedIn, Apple)
- Passwordless authentication (magic links)
- Biometric authentication support
- Advanced session management (device management)
- Anomaly detection for suspicious logins

**Phase 4 (12+ months):**
- Multi-region deployment
- Advanced fraud detection
- Identity verification integration
- Enterprise SSO support (SAML, OIDC)
- Federated identity management

## Conclusion

This design provides a secure, scalable foundation for user registration and authentication in the Yomite application. The architecture supports the immediate needs while remaining flexible for future enhancements. The emphasis on property-based testing ensures correctness across all scenarios, while the modular design enables independent scaling and deployment of components.

Key strengths of this design:
- Security-first approach with multiple layers of protection
- Comprehensive testing strategy with property-based tests
- Cloud-agnostic design with AWS implementation
- Clear separation of concerns for maintainability
- Scalable architecture supporting future growth

The design addresses all requirements from the requirements document and provides a clear path for implementation and testing.

