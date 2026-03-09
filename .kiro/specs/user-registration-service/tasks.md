# Implementation Plan: User Registration Service

## Overview

This implementation plan breaks down the User Registration Service into discrete, actionable coding tasks. The service provides secure user identity management through social login integration, including registration, authentication, session management, and account linking.

The implementation follows a bottom-up approach: core infrastructure and data models first, then service components, API layer, testing, containerization, and finally infrastructure as code.

## Tasks

- [ ] 1. Project setup and core infrastructure
  - Create project directory structure following modular architecture
  - Set up Python virtual environment and dependency management (requirements.txt or pyproject.toml)
  - Configure pytest for unit and property-based testing with Hypothesis
  - Create shared configuration module for environment variables
  - Set up logging infrastructure with structured JSON logging
  - _Requirements: 9.4, 8.1_

- [ ] 2. Database schema and models
  - [ ] 2.1 Create database schema SQL files
    - Write PostgreSQL schema for user_accounts table with UUID primary key
    - Write PostgreSQL schema for social_identities table with foreign key constraints
    - Add indexes for email lookup and social identity lookup
    - Add email format validation constraint
    - _Requirements: 11.1, 11.4, 11.5_
  
  - [ ] 2.2 Implement User Account data models
    - Create UserAccount dataclass with user_id, email, timestamps, and social_identities list
    - Create SocialIdentity dataclass with provider, provider_user_id, and linked_at
    - Add validation methods for email format
    - _Requirements: 1.5, 2.4_
  
  - [ ]* 2.3 Write property test for User Account models
    - **Property 7: Account Persistence Round-Trip**
    - **Validates: Requirements 1.5, 11.1**
  
  - [ ] 2.3 Implement database connection and repository layer
    - Create database connection manager with connection pooling
    - Implement UserRepository with methods: create_user, find_by_email, link_provider
    - Add retry logic for transient database errors (max 3 attempts, exponential backoff)
    - Handle database constraint violations gracefully
    - _Requirements: 11.1, 11.3, 11.5_
  
  - [ ]* 2.4 Write property test for database operations
    - **Property 21: Database Constraint Enforcement**
    - **Validates: Requirements 11.5**
  
  - [ ]* 2.5 Write property test for database error handling
    - **Property 22: Database Error Handling**
    - **Validates: Requirements 11.3**

- [ ] 3. Session storage and models
  - [ ] 3.1 Create Session data models
    - Create Session dataclass with token, user_id, timestamps, client_ip, user_agent, rotation_count
    - Create SessionValidation dataclass with valid, user_id, expires_at, requires_reauth
    - Create ClientMetadata dataclass with ip_address and user_agent
    - _Requirements: 4.1, 7.2_
  
  - [ ] 3.2 Implement Redis session store
    - Create RedisSessionStore class with connection management
    - Implement store_session method with TTL-based expiration
    - Implement get_session method with automatic expiration handling
    - Implement delete_session method for logout
    - Use hash-based storage with session:{token_hash} key pattern
    - _Requirements: 11.2, 4.5_
  
  - [ ]* 3.3 Write unit tests for session store
    - Test session creation, retrieval, and deletion
    - Test TTL expiration behavior
    - Test connection error handling
    - _Requirements: 11.2_

- [ ] 4. Token generation and security
  - [ ] 4.1 Implement secure token generator
    - Create TokenGenerator class using secrets module for cryptographic randomness
    - Generate 256-bit random tokens encoded as base64url
    - Add version prefix (v1.) for future token format changes
    - Ensure token uniqueness across all generated tokens
    - _Requirements: 3.5, 7.1_
  
  - [ ]* 4.2 Write property test for token entropy
    - **Property 10: Session Token Entropy**
    - **Validates: Requirements 3.5, 7.1**
  
  - [ ] 4.3 Implement token hashing for storage
    - Create hash_token function using SHA-256
    - Use hashed tokens as Redis keys to prevent token leakage
    - _Requirements: 7.1_

- [ ] 5. OAuth client manager
  - [ ] 5.1 Create OAuth configuration and data models
    - Create OAuthToken dataclass with access_token, token_type, expires_in, refresh_token
    - Create UserProfile dataclass with provider, provider_user_id, email, name, picture_url
    - Create OAuthConfig dataclass for provider-specific settings
    - Load OAuth credentials from environment variables or secrets manager
    - _Requirements: 1.1, 1.4_
  
  - [ ] 5.2 Implement OAuth client for Google
    - Create GoogleOAuthClient class implementing OAuth 2.0 authorization code flow
    - Implement get_authorization_url method with state parameter
    - Implement exchange_code_for_token method
    - Implement get_user_profile method using Google People API
    - Handle OAuth errors and map to standardized error types
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ] 5.3 Implement OAuth client for Facebook
    - Create FacebookOAuthClient class implementing OAuth 2.0 authorization code flow
    - Implement get_authorization_url, exchange_code_for_token, get_user_profile methods
    - Handle Facebook-specific error responses
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [ ] 5.4 Implement OAuth client for GitHub
    - Create GitHubOAuthClient class implementing OAuth 2.0 authorization code flow
    - Implement get_authorization_url, exchange_code_for_token, get_user_profile methods
    - Handle GitHub-specific error responses
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [ ] 5.5 Create OAuthClientManager factory
    - Implement OAuthClientManager class with get_client method
    - Support provider selection (google, facebook, github)
    - Return appropriate OAuth client based on provider name
    - Raise InvalidProviderError for unsupported providers
    - _Requirements: 1.4_
  
  - [ ]* 5.6 Write property test for OAuth flow initiation
    - **Property 1: OAuth Flow Initiation**
    - **Validates: Requirements 1.1, 3.1**
  
  - [ ]* 5.7 Write property test for provider error propagation
    - **Property 3: Provider Error Propagation**
    - **Validates: Requirements 1.3**
  
  - [ ]* 5.8 Write unit tests for OAuth clients
    - Test authorization URL generation with state parameter
    - Test token exchange with mock provider responses
    - Test user profile retrieval
    - Test error handling for various OAuth error scenarios
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 6. Mock OAuth providers for local development
  - [ ] 6.1 Implement mock OAuth provider
    - Create MockOAuthProvider class for local testing
    - Implement authorize, exchange_code, get_profile methods
    - Support error simulation for testing error handling
    - Return configurable mock user profiles
    - _Requirements: 9.2, 9.5_
  
  - [ ]* 6.2 Write unit tests for mock provider
    - Test mock authorization flow
    - Test error simulation
    - Test configurable user profiles
    - _Requirements: 9.2_

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Registration Service implementation
  - [ ] 8.1 Implement input validation
    - Create InputValidator class with methods for sanitizing inputs
    - Validate redirect URIs against allowed patterns
    - Detect and reject SQL injection patterns
    - Detect and reject XSS patterns (script tags, event handlers)
    - _Requirements: 6.5_
  
  - [ ]* 8.2 Write property test for input validation
    - **Property 16: Input Validation**
    - **Validates: Requirements 6.5**
  
  - [ ] 8.3 Implement account linking logic
    - Create AccountLinker class with link_provider method
    - Check for existing accounts by email
    - Add new social identity to existing account
    - Return linked status and notification message
    - _Requirements: 2.1, 2.2_
  
  - [ ]* 8.4 Write property test for account linking
    - **Property 4: Account Linking for Duplicate Emails**
    - **Validates: Requirements 2.1**
  
  - [ ]* 8.5 Write property test for account linking notification
    - **Property 5: Account Linking Notification**
    - **Validates: Requirements 2.2**
  
  - [ ] 8.6 Implement RegistrationService
    - Create RegistrationService class with register_with_provider method
    - Orchestrate OAuth flow using OAuthClientManager
    - Validate inputs using InputValidator
    - Check for existing accounts with same email and provider
    - Create new user account or link provider using AccountLinker
    - Return RegistrationResult with user_id, email, linked status
    - Log all registration attempts with success/failure status
    - _Requirements: 1.1, 1.2, 1.5, 2.1, 2.2, 2.3, 8.2_
  
  - [ ]* 8.7 Write property test for account creation
    - **Property 2: Account Creation from Valid Credentials**
    - **Validates: Requirements 1.2, 1.5**
  
  - [ ]* 8.8 Write property test for duplicate provider error
    - **Property 6: Duplicate Provider Registration Error**
    - **Validates: Requirements 2.3**
  
  - [ ]* 8.9 Write unit tests for RegistrationService
    - Test successful registration with new email
    - Test account linking with existing email, different provider
    - Test error when registering with existing email and provider
    - Test OAuth error handling
    - Test input validation errors
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [ ] 9. Session Manager implementation
  - [ ] 9.1 Implement SessionManager core functionality
    - Create SessionManager class with create_session method
    - Generate secure tokens using TokenGenerator
    - Store session data in Redis with client metadata binding
    - Set configurable expiration time (default 24 hours, max 24 hours)
    - Return Session with token and expiration
    - _Requirements: 4.1, 7.1, 7.2, 7.5_
  
  - [ ]* 9.2 Write property test for session expiration
    - **Property 11: Session Expiration Configuration**
    - **Validates: Requirements 4.1, 7.5**
  
  - [ ] 9.3 Implement session validation
    - Add validate_session method to SessionManager
    - Retrieve session from Redis by hashed token
    - Check token expiration
    - Validate client metadata (IP address and user agent) matches stored values
    - Return SessionValidation with validity status and user_id
    - Raise InvalidTokenError for invalid/expired tokens
    - Raise MetadataMismatchError for metadata mismatches
    - _Requirements: 4.2, 4.3, 4.4, 7.3_
  
  - [ ]* 9.4 Write property test for session validation
    - **Property 12: Session Validation**
    - **Validates: Requirements 4.2, 4.3, 4.4, 7.3**
  
  - [ ]* 9.5 Write property test for session metadata binding
    - **Property 17: Session Metadata Binding**
    - **Validates: Requirements 7.2**
  
  - [ ] 9.6 Implement session invalidation
    - Add invalidate_session method to SessionManager
    - Delete session from Redis by hashed token
    - Return success status
    - Log logout events
    - _Requirements: 5.1, 5.2, 8.4_
  
  - [ ]* 9.7 Write property test for session invalidation
    - **Property 13: Session Invalidation on Logout**
    - **Validates: Requirements 5.1, 5.2**
  
  - [ ] 9.8 Implement token rotation
    - Add rotate_token method to SessionManager
    - Validate old token and client metadata
    - Generate new token
    - Update session in Redis with new token
    - Invalidate old token
    - Increment rotation_count
    - Return new Session
    - _Requirements: 7.4_
  
  - [ ]* 9.9 Write property test for token rotation
    - **Property 18: Token Rotation**
    - **Validates: Requirements 7.4**
  
  - [ ]* 9.10 Write unit tests for SessionManager
    - Test session creation with various expiration times
    - Test session validation with valid and invalid tokens
    - Test session validation with metadata mismatches
    - Test session invalidation
    - Test token rotation
    - Test expired session handling
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 7.2, 7.3, 7.4, 7.5_

- [ ] 10. Authentication Service implementation
  - [ ] 10.1 Implement AuthenticationService
    - Create AuthenticationService class with authenticate_with_provider method
    - Orchestrate OAuth flow using OAuthClientManager
    - Query UserRepository to find existing account by email and provider
    - Create session using SessionManager with client metadata
    - Return AuthenticationResult with session_token, user_id, expires_at
    - Raise UserNotFoundError if no account exists
    - Log all authentication attempts with success/failure status
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 8.3_
  
  - [ ]* 10.2 Write property test for session creation on authentication
    - **Property 8: Session Creation on Successful Authentication**
    - **Validates: Requirements 3.2, 3.4**
  
  - [ ]* 10.3 Write property test for authentication error
    - **Property 9: Authentication Error for Non-Existent Accounts**
    - **Validates: Requirements 3.3**
  
  - [ ]* 10.4 Write unit tests for AuthenticationService
    - Test successful authentication with existing account
    - Test authentication failure with non-existent account
    - Test OAuth error handling
    - Test session creation integration
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Rate limiting implementation
  - [ ] 12.1 Implement rate limiter
    - Create RateLimiter class using sliding window algorithm
    - Store request counts in Redis with client IP as key
    - Configure limits per endpoint (e.g., 10 requests per minute for auth endpoints)
    - Implement check_rate_limit method returning allowed/denied status
    - Return time until reset when limit exceeded
    - _Requirements: 6.3, 6.4_
  
  - [ ]* 12.2 Write property test for rate limiting
    - **Property 15: Rate Limiting Enforcement**
    - **Validates: Requirements 6.3, 6.4**
  
  - [ ]* 12.3 Write unit tests for rate limiter
    - Test request counting within time window
    - Test limit enforcement
    - Test window reset behavior
    - Test multiple clients independently
    - _Requirements: 6.3, 6.4_

- [ ] 13. Error handling and response models
  - [ ] 13.1 Create error classes and response models
    - Create custom exception classes: InvalidProviderError, OAuthError, AccountExistsError, UserNotFoundError, InvalidTokenError, MetadataMismatchError, RateLimitError, ValidationError
    - Create APIResponse dataclass with success, data, error, request_id
    - Create APIError dataclass with code, message, details
    - Define error code constants matching design document
    - _Requirements: 12.1, 12.3, 12.4_
  
  - [ ] 13.2 Implement error handler middleware
    - Create ErrorHandler class to catch and format exceptions
    - Map exception types to HTTP status codes
    - Format errors as APIResponse with APIError
    - Include request_id in all responses
    - Ensure sensitive data is not included in error messages
    - Log errors with full context
    - _Requirements: 8.1, 8.5, 12.3, 12.4, 12.5_
  
  - [ ]* 13.3 Write property test for error status codes
    - **Property 25: Error Status Codes**
    - **Validates: Requirements 12.3, 12.4**
  
  - [ ]* 13.4 Write property test for sensitive data exclusion
    - **Property 20: Sensitive Data Exclusion from Logs**
    - **Validates: Requirements 8.5**
  
  - [ ]* 13.5 Write unit tests for error handling
    - Test exception to status code mapping
    - Test error response formatting
    - Test request_id inclusion
    - Test sensitive data exclusion from logs
    - _Requirements: 8.1, 8.5, 12.3, 12.4, 12.5_

- [ ] 14. API endpoints and controllers
  - [ ] 14.1 Implement registration endpoint
    - Create POST /auth/register/{provider} endpoint
    - Accept redirect_uri in request body
    - Validate provider parameter
    - Apply rate limiting
    - Call RegistrationService.register_with_provider
    - Return APIResponse with user_id, email, linked status
    - Handle errors and return appropriate status codes
    - Add request_id to response
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 6.3, 12.1, 12.2, 12.5_
  
  - [ ] 14.2 Implement login endpoint
    - Create POST /auth/login/{provider} endpoint
    - Accept redirect_uri in request body
    - Extract client IP and user agent from request headers
    - Validate provider parameter
    - Apply rate limiting
    - Call AuthenticationService.authenticate_with_provider
    - Return APIResponse with session_token, user_id, expires_at
    - Handle errors and return appropriate status codes
    - Add request_id to response
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 6.3, 12.1, 12.2, 12.5_
  
  - [ ] 14.3 Implement logout endpoint
    - Create POST /auth/logout endpoint
    - Accept session_token in request body
    - Call SessionManager.invalidate_session
    - Return APIResponse with success status
    - Handle errors and return appropriate status codes
    - Add request_id to response
    - _Requirements: 5.1, 5.2, 5.3, 12.1, 12.2, 12.5_
  
  - [ ] 14.4 Implement session validation endpoint
    - Create GET /auth/validate endpoint
    - Extract session_token from Authorization header (Bearer token)
    - Extract client IP and user agent from request headers
    - Call SessionManager.validate_session
    - Return APIResponse with valid status, user_id, expires_at
    - Handle errors and return appropriate status codes
    - Add request_id to response
    - _Requirements: 4.2, 4.3, 4.4, 12.1, 12.2, 12.5_
  
  - [ ]* 14.5 Write property test for JSON response format
    - **Property 23: JSON Response Format**
    - **Validates: Requirements 12.1**
  
  - [ ]* 14.6 Write property test for success status codes
    - **Property 24: Success Status Codes**
    - **Validates: Requirements 12.2**
  
  - [ ]* 14.7 Write property test for request tracing
    - **Property 26: Request Tracing**
    - **Validates: Requirements 12.5**
  
  - [ ]* 14.8 Write property test for operation logging
    - **Property 19: Operation Logging**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
  
  - [ ]* 14.9 Write integration tests for API endpoints
    - Test complete registration flow with mock OAuth provider
    - Test complete authentication flow
    - Test logout flow
    - Test session validation flow
    - Test error scenarios for each endpoint
    - Test rate limiting across endpoints
    - _Requirements: 1.1, 1.2, 3.1, 3.2, 4.2, 5.1, 6.3_

- [ ] 15. API Gateway and HTTPS enforcement
  - [ ] 15.1 Create API Gateway configuration
    - Configure Flask or FastAPI application with CORS support
    - Add middleware for HTTPS enforcement (reject HTTP requests)
    - Add middleware for request ID generation
    - Add middleware for rate limiting
    - Add middleware for error handling
    - Configure request logging
    - _Requirements: 6.1, 6.2, 12.5_
  
  - [ ]* 15.2 Write unit tests for HTTPS enforcement
    - Test HTTP request rejection
    - Test HTTPS request acceptance
    - _Requirements: 6.1, 6.2_
  
  - [ ] 15.3 Create health check endpoint
    - Create GET /health endpoint
    - Check database connectivity
    - Check Redis connectivity
    - Return 200 if healthy, 503 if unhealthy
    - _Requirements: 9.5_

- [ ] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Docker containerization
  - [ ] 17.1 Create Dockerfile for application
    - Create multi-stage Dockerfile with Python 3.11+ base image
    - Install dependencies from requirements.txt
    - Copy application code
    - Set up non-root user for security
    - Expose port 8000
    - Define CMD to run application server
    - _Requirements: 9.1_
  
  - [ ] 17.2 Create Docker Compose configuration
    - Create docker-compose.yml with services: postgres, redis, registration-service, api-gateway
    - Configure PostgreSQL with initialization script
    - Configure Redis with persistence
    - Configure application with environment variables
    - Set up volume mounts for local development
    - Configure networking between services
    - _Requirements: 9.1, 9.3, 9.5_
  
  - [ ] 17.3 Create database initialization script
    - Create init-db.sql with schema creation
    - Include user_accounts and social_identities tables
    - Include indexes and constraints
    - _Requirements: 11.1, 11.4, 11.5_
  
  - [ ] 17.4 Create environment configuration files
    - Create .env.example with all required environment variables
    - Document each variable with comments
    - Create separate configs for development, staging, production
    - _Requirements: 9.4_
  
  - [ ]* 17.5 Test Docker setup
    - Build Docker images successfully
    - Start all services with docker-compose up
    - Verify database connectivity
    - Verify Redis connectivity
    - Run health check endpoint
    - _Requirements: 9.1, 9.5_

- [ ] 18. Infrastructure as Code with AWS CDK
  - [ ] 18.1 Set up CDK project structure
    - Initialize CDK project with TypeScript
    - Create directory structure: bin/, lib/stacks/, lib/constructs/, lib/config/
    - Configure cdk.json with app entry point
    - _Requirements: 10.1, 10.2_
  
  - [ ] 18.2 Implement network stack
    - Create NetworkStack with VPC, public/private subnets, NAT gateway
    - Configure security groups for application, database, and cache
    - Set up Internet Gateway and route tables
    - _Requirements: 10.3, 10.4_
  
  - [ ] 18.3 Implement database stack
    - Create DatabaseStack with RDS PostgreSQL instance
    - Configure Multi-AZ deployment for high availability
    - Set up automated backups with 7-day retention
    - Configure security group allowing access from application subnet
    - Store database credentials in Secrets Manager
    - _Requirements: 10.3, 11.1_
  
  - [ ] 18.4 Implement cache stack
    - Create CacheStack with ElastiCache Redis cluster
    - Configure cluster mode for high availability
    - Enable encryption at rest and in transit
    - Configure security group allowing access from application subnet
    - _Requirements: 10.3, 11.2_
  
  - [ ] 18.5 Implement compute stack
    - Create ComputeStack with ECS Fargate cluster
    - Configure Application Load Balancer with HTTPS listener
    - Set up target groups for service routing
    - Configure auto-scaling policies based on CPU/memory
    - _Requirements: 10.3, 10.5_
  
  - [ ] 18.6 Implement service stack
    - Create ServiceStack with ECS task definitions for registration, authentication, session services
    - Configure container images from ECR
    - Set up environment variables and secrets from Secrets Manager
    - Configure CloudWatch log groups
    - Set up health checks
    - Configure desired count and auto-scaling
    - _Requirements: 10.3, 10.5_
  
  - [ ] 18.7 Create environment-specific configurations
    - Create dev.ts, staging.ts, prod.ts configuration files
    - Define environment-specific parameters (instance sizes, counts, etc.)
    - _Requirements: 10.2_
  
  - [ ] 18.8 Create CDK deployment scripts
    - Create scripts for deploying to different environments
    - Document deployment process in README
    - _Requirements: 10.2_

- [ ] 19. Documentation
  - [ ] 19.1 Create API documentation
    - Document all API endpoints with request/response examples
    - Include error codes and their meanings
    - Provide example curl commands
    - Document authentication flow
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ] 19.2 Create local development guide
    - Document prerequisites (Docker, Python, etc.)
    - Provide step-by-step setup instructions
    - Document how to run tests
    - Document how to use mock OAuth providers
    - Include troubleshooting section
    - _Requirements: 9.4, 9.5_
  
  - [ ] 19.3 Create deployment guide
    - Document AWS prerequisites
    - Provide CDK deployment instructions
    - Document environment variable configuration
    - Document secrets management
    - Include rollback procedures
    - _Requirements: 10.1, 10.2_
  
  - [ ] 19.4 Update project README
    - Add project overview and architecture diagram
    - Link to detailed documentation
    - Include quick start guide
    - Document technology stack
    - _Requirements: 9.4_

- [ ] 20. Observability and monitoring setup
  - [ ] 20.1 Create monitoring proposal document
    - Document recommended CloudWatch metrics (request rate, error rate, response time, etc.)
    - Document recommended CloudWatch alarms (critical and warning levels)
    - Document log aggregation strategy
    - Document distributed tracing approach (AWS X-Ray or similar)
    - Provide cost estimates for monitoring infrastructure
    - _Requirements: 8.1_
  
  - [ ] 20.2 Create CI/CD pipeline proposal document
    - Document recommended CI/CD pipeline stages (lint, test, build, deploy)
    - Recommend CI/CD platform (GitHub Actions, GitLab CI, AWS CodePipeline)
    - Document automated testing strategy in pipeline
    - Document deployment strategies (blue-green, canary)
    - Document rollback procedures
    - Provide implementation timeline estimate
    - _Requirements: 10.2_

- [ ] 21. Final checkpoint and validation
  - Run complete test suite (unit, property-based, integration)
  - Verify all 26 correctness properties are tested
  - Test complete registration and authentication flows locally
  - Verify Docker setup works end-to-end
  - Review all documentation for completeness
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Property-based tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests validate complete user flows
- The implementation follows a bottom-up approach: infrastructure → services → API → deployment
- Mock OAuth providers enable local development without external dependencies
- All 26 correctness properties from the design document are covered by property-based tests
- Checkpoints ensure incremental validation and provide opportunities for user feedback
- CI/CD and observability are documented as proposals rather than implemented to focus on core functionality
