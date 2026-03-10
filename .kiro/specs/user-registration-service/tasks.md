# Implementation Plan: User Registration Service (Serverless with Cognito)

## Overview

This plan implements a serverless user registration and authentication service using AWS Cognito, Lambda, DynamoDB, and API Gateway. AWS Cognito handles social login (Google, Facebook) and JWT-based session management. Lambda functions focus on business logic (user profiles). Implementation uses Python 3.11+, AWS SAM for infrastructure, and pip for dependency management.

## Tasks

- [x] 1. Set up project structure and development environment
  - Create directory structure for Lambda handlers, services, models, and utilities
  - Set up uvx for Python dependency management
  - Create requirements.txt and requirements-dev.txt
  - Configure AWS SAM template (template.yaml) with basic structure
  - Set up local development with Docker Compose (DynamoDB Local)
  - Create .gitignore for Python and AWS artifacts
  - _Requirements: 9.1, 9.4, 9.5, 10.1_

- [x] 2. Implement core data models and DynamoDB schema
  - [x] 2.1 Create Python data classes for all entities
    - Implement UserAccount, SocialIdentity, Session, ClientMetadata dataclasses
    - Implement RegistrationResult, AuthenticationResult, SessionValidation dataclasses
    - Implement OAuthToken, UserProfile, APIResponse, APIError dataclasses
    - Define ErrorCodes constants class
    - _Requirements: 11.1, 11.4_

  - [ ]* 2.2 Write property test for data model round-trip consistency
    - **Property 7: Account Persistence Round-Trip**
    - **Validates: Requirements 1.5, 11.1**

  - [x] 2.3 Implement DynamoDB client wrapper
    - Create DynamoDBClient class with connection pooling
    - Implement methods for PutItem, GetItem, Query, UpdateItem, DeleteItem
    - Add retry logic with exponential backoff for throttling
    - Implement error handling for DynamoDB exceptions
    - _Requirements: 11.3, 11.4_

  - [ ]* 2.4 Write property test for DynamoDB error handling
    - **Property 22: Database Error Handling**
    - **Validates: Requirements 11.3**

- [x] 3. Implement input validation and security utilities
  - [x] 3.1 Create InputValidator class
    - Implement email validation with regex
    - Implement provider validation (google, facebook, github)
    - Implement string sanitization (remove null bytes, control characters)
    - Implement injection detection (XSS, script injection patterns)
    - _Requirements: 6.5_

  - [ ]* 3.2 Write property test for input validation
    - **Property 16: Input Validation**
    - **Validates: Requirements 6.5**

  - [x] 3.3 Create session token generation utilities
    - Implement generate_session_token() with 256-bit entropy
    - Implement hash_token() using SHA-256
    - Add token format versioning (v1.{random_string})
    - _Requirements: 3.5, 7.1_

  - [ ]* 3.4 Write property test for session token entropy
    - **Property 10: Session Token Entropy**
    - **Validates: Requirements 3.5, 7.1**

- [x] 4. Implement structured logging and error handling
  - [x] 4.1 Create StructuredLogger class
    - Implement JSON logging with timestamp, level, service, event
    - Add log sanitization to remove sensitive data (tokens, passwords)
    - Support log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - _Requirements: 8.1, 8.5_

  - [ ]* 4.2 Write property test for sensitive data exclusion from logs
    - **Property 20: Sensitive Data Exclusion from Logs**
    - **Validates: Requirements 8.5**

  - [x] 4.3 Implement error handling utilities
    - Create handle_dynamodb_error() function
    - Create handle_oauth_error() function
    - Implement retry_with_backoff decorator
    - Define standard API error response format
    - _Requirements: 8.1, 11.3_

- [ ] 5. Checkpoint - Verify core utilities
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement user profile handler (Cognito-based)
  - [x] 6.1 Create profile_handler Lambda function
    - Implement lambda_handler(event, context) entry point
    - Extract Cognito user context from API Gateway authorizer JWT claims
    - Implement GET /profile endpoint (retrieve or create from Cognito data)
    - Implement PUT /profile endpoint (update user profile)
    - Store user profiles in DynamoDB (PK: USER#{sub}, SK: PROFILE)
    - Add structured logging for profile operations
    - Handle errors and return appropriate HTTP status codes
    - _Requirements: 1.2, 1.5, 8.2, 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ]* 6.2 Write unit tests for profile handler
    - Test GET /profile with existing profile
    - Test GET /profile with new user (auto-create from Cognito)
    - Test PUT /profile with valid updates
    - Test error handling for invalid requests
    - Mock Cognito JWT claims extraction

  - [ ]* 6.3 Write integration test for profile operations
    - Test complete profile lifecycle (create, read, update)
    - Test with mock Cognito authorizer context
    - Verify DynamoDB operations

- [ ] 7. Checkpoint - Verify profile handler
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Complete AWS SAM infrastructure template with Cognito
  - [x] 8.1 Define Cognito User Pool in SAM template
    - Configure User Pool with email verification
    - Add Google Identity Provider integration
    - Add Facebook Identity Provider integration
    - Configure User Pool Client with OAuth settings
    - Configure User Pool Domain for Hosted UI
    - Set token validity (Access: 1h, ID: 1h, Refresh: 30d)
    - _Requirements: 1.1, 3.1, 4.1, 10.1_

  - [x] 8.2 Define DynamoDB table in SAM template (simplified)
    - Configure table with PK (String), SK (String)
    - Set BillingMode to PAY_PER_REQUEST (on-demand)
    - Enable PointInTimeRecovery for production
    - Add appropriate tags (Environment, Service)
    - Note: No GSIs needed (Cognito handles user lookup)
    - Note: No TTL needed (no session storage)
    - _Requirements: 10.1, 10.3, 11.1_

  - [x] 8.3 Define Lambda function in SAM template
    - Configure user-profile-handler (256 MB, 10s timeout, ARM64)
    - Add DynamoDB table permissions via IAM policies
    - Configure environment variables (DYNAMODB_TABLE_NAME, USER_POOL_ID, ENVIRONMENT, LOG_LEVEL)
    - Enable X-Ray tracing
    - _Requirements: 10.1, 10.3_

  - [x] 8.4 Define API Gateway with Cognito Authorizer
    - Configure HTTP API with CORS settings
    - Configure Cognito Authorizer (validates JWT automatically)
    - Define GET /profile endpoint → user-profile-handler
    - Define PUT /profile endpoint → user-profile-handler
    - Configure throttling settings (burst: 100, rate: 50 RPS)
    - Enable CloudWatch Logs for API Gateway
    - _Requirements: 4.2, 6.1, 6.2, 6.3, 10.1, 10.3_

  - [x] 8.5 Define CloudWatch Log Groups
    - Create log group for user-profile-handler
    - Set retention periods (7 days dev, 30 days prod)
    - _Requirements: 8.1_

  - [ ] 8.6 Create environment-specific parameter files
    - Create samconfig.toml with dev/staging/prod configurations
    - Configure OAuth secret ARNs for each environment in Secrets Manager
    - Set stack names, regions, and capabilities
    - _Requirements: 10.1, 10.2_

- [x] 9. Set up local development environment
  - [x] 9.1 Create docker-compose.yml for local services
    - Add DynamoDB Local service (port 8000)
    - Configure network and volumes
    - _Requirements: 9.1, 9.3_

  - [x] 9.2 Create local testing scripts
    - Create scripts/setup-local-dynamodb.py to create local table (simplified)
    - _Requirements: 9.1, 9.4, 9.5_

  - [x] 9.3 Create local environment configuration
    - Create .env.example with Cognito configuration
    - Document Cognito User Pool setup for local testing
    - _Requirements: 9.4_

  - [ ] 9.4 Document local testing with Cognito
    - Document Cognito Local setup or mocking strategy
    - Create mock JWT tokens for local testing
    - Document how to test profile handler locally
    - _Requirements: 9.4_

- [ ] 10. Implement monitoring and observability
  - [ ] 10.1 Add X-Ray tracing to Lambda function
    - Import aws-xray-sdk and patch all libraries
    - Add @xray_recorder.capture decorators to key functions
    - Add metadata and annotations to traces
    - _Requirements: 8.1_

  - [ ] 10.2 Implement custom CloudWatch metrics
    - Create put_custom_metric() utility function
    - Add metrics for profile operations (get, update)
    - Add metrics for DynamoDB latency
    - Add metrics for Cognito authorization failures
    - _Requirements: 8.1_

  - [ ] 10.3 Create CloudWatch dashboard configuration
    - Define dashboard JSON with Lambda metrics
    - Add DynamoDB consumed capacity metrics
    - Add API Gateway request metrics
    - Add Cognito User Pool metrics
    - Add log insights queries for recent errors
    - _Requirements: 8.1_

- [ ] 11. Checkpoint - Verify infrastructure and monitoring
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Create deployment and operations documentation
  - [ ] 12.1 Update README.md with Cognito architecture
    - Document Cognito-based authentication flow
    - Provide OAuth provider setup instructions (Google, Facebook)
    - Document deployment procedures for each environment
    - Include troubleshooting guide for Cognito issues
    - _Requirements: 9.4, 10.1_

  - [ ] 12.2 Create DEPLOYMENT.md with deployment guide
    - Document prerequisites (AWS CLI, SAM CLI, credentials)
    - Document Cognito User Pool setup steps
    - Document OAuth provider configuration in AWS Secrets Manager
    - Provide step-by-step deployment instructions
    - Document environment-specific configurations
    - Include rollback procedures
    - _Requirements: 10.1, 10.2_

  - [ ] 12.3 Create OPERATIONS.md with operational runbook
    - Document monitoring and alerting setup
    - Provide troubleshooting procedures for Cognito issues
    - Document disaster recovery procedures
    - Include cost optimization recommendations
    - _Requirements: 8.1_

  - [ ] 12.4 Update tech.md with actual dependencies
    - Document all Python dependencies and versions
    - Document AWS services (Cognito, Lambda, DynamoDB, API Gateway)
    - Add common commands for build, test, deploy
    - _Requirements: 10.1_

- [ ] 13. Create CI/CD pipeline configuration
  - [ ] 13.1 Create GitHub Actions workflow
    - Add workflow for linting (flake8) and type checking (mypy)
    - Add workflow for unit tests with coverage
    - Add workflow for integration tests
    - Add workflow for deployment to staging (on develop branch)
    - Add workflow for deployment to production (on main branch)
    - _Requirements: 10.1, 10.2_

  - [ ] 13.2 Configure test coverage reporting
    - Set up pytest with coverage plugin
    - Configure codecov integration
    - Set minimum coverage threshold (80%)
    - _Requirements: 8.1_

- [ ] 14. Implement security hardening
  - [ ] 14.1 Create IAM policies with least privilege
    - Define Lambda execution role with minimal DynamoDB permissions
    - Add CloudWatch Logs permissions
    - Add X-Ray permissions
    - Add Cognito User Pool read permissions (if needed)
    - _Requirements: 6.1, 6.2_

  - [ ] 14.2 Configure OAuth secrets in AWS Secrets Manager
    - Create secrets for Google OAuth client ID and secret
    - Create secrets for Facebook OAuth client ID and secret
    - Reference secrets in Cognito Identity Provider configuration
    - Document secret rotation procedures
    - _Requirements: 6.1_

  - [ ] 14.3 Add security scanning to CI/CD
    - Add dependency vulnerability scanning (safety, pip-audit)
    - Add SAST scanning for code (bandit)
    - Add secrets scanning (detect-secrets)
    - _Requirements: 6.5_

- [ ] 15. Final integration testing and validation
  - [ ] 15.1 Run complete end-to-end tests locally
    - Test profile operations (GET, PUT) with mock Cognito JWT
    - Test error scenarios and edge cases
    - Verify DynamoDB operations

  - [ ] 15.2 Deploy to development environment
    - Deploy SAM stack to AWS dev environment
    - Verify Cognito User Pool is created
    - Verify Identity Providers (Google, Facebook) are configured
    - Verify Lambda function is created
    - Verify DynamoDB table is created with correct schema
    - Verify API Gateway endpoints are accessible
    - Run smoke tests against dev environment

  - [ ] 15.3 Test Cognito authentication flow
    - Test Google OAuth login via Cognito Hosted UI
    - Test Facebook OAuth login via Cognito Hosted UI
    - Verify JWT tokens are issued correctly
    - Test API calls with JWT tokens
    - Verify API Gateway Cognito Authorizer validates tokens

  - [ ] 15.4 Perform load testing
    - Use artillery or locust for load testing
    - Test profile endpoint at 50 RPS
    - Verify no throttling or errors under load
    - Monitor CloudWatch metrics during load test

- [ ] 16. Final checkpoint - Production readiness
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Integration tests validate complete flows end-to-end
- All Lambda functions use Python 3.11+ and ARM64 (Graviton2) for cost optimization
- DynamoDB uses on-demand billing for cost efficiency at current scale
- Local development uses DynamoDB Local and SAM Local for production-like testing
- Infrastructure as Code uses AWS SAM for simplified serverless deployment

## Architecture Notes

**Cognito-Based Authentication:**
- AWS Cognito handles OAuth flows with social providers (Google, Facebook)
- Cognito issues JWT tokens (ID, Access, Refresh) for authentication
- API Gateway Cognito Authorizer validates JWT tokens automatically
- No custom OAuth client code needed
- No custom session management code needed
- Lambda functions focus on business logic only (user profiles)

**Simplified Infrastructure:**
- Single Lambda function (user-profile-handler) for profile operations
- Simplified DynamoDB table (no GSIs, no session storage)
- Cognito User Pool with Identity Providers
- API Gateway with Cognito Authorizer

**Cost Optimization:**
- Cognito: ~$5-10/month (50 MAU free tier)
- Lambda: ~$3/month (1M requests free tier)
- DynamoDB: ~$1/month (25 GB free tier)
- API Gateway: ~$3/month (1M requests free tier)
- Total: ~$15-25/month (with free tier benefits)
