# Cognito Refactor Status

## Overview

Refactoring from custom OAuth implementation to AWS Cognito User Pools for managed authentication.

**Decision Reference:** See DECISIONS.md - Decision 12

**Status:** In Progress (Core implementation complete, documentation updates remaining)

**Last Updated:** 2026-03-09

---

## Completed Work ✅

### 1. Architecture Decision
- ✅ Added Decision 12 to DECISIONS.md documenting Cognito switch
- ✅ Documented rationale, cost comparison, and trade-offs
- ✅ Created .config.kiro to track refactor status

### 2. Infrastructure (SAM Template)
- ✅ Added Cognito User Pool with email verification
- ✅ Added Cognito User Pool Client with OAuth configuration
- ✅ Added Cognito User Pool Domain for hosted UI
- ✅ Added Google Identity Provider integration
- ✅ Added Facebook Identity Provider integration
- ✅ Configured API Gateway Cognito Authorizer for automatic JWT validation
- ✅ Simplified Lambda functions (removed OAuth/session handlers)
- ✅ Simplified DynamoDB table (removed session storage, removed GSIs)
- ✅ Updated to single UserProfileHandler Lambda function

### 3. Data Models
- ✅ Added CognitoUserContext for JWT claims
- ✅ Simplified UserProfile (removed OAuth-specific fields)
- ✅ Removed Session model (no longer needed)
- ✅ Removed SocialIdentity model (Cognito handles this)
- ✅ Removed OAuth-related models (OAuthToken, etc.)

### 4. Error Codes
- ✅ Removed OAuth-specific error codes
- ✅ Updated error codes for Cognito architecture
- ✅ Added format_error_response helper for API Gateway

### 5. Lambda Handlers
- ✅ Created profile_handler.py for user profile operations
- ✅ Implements GET /profile (retrieve or create from Cognito data)
- ✅ Implements PUT /profile (update user profile)
- ✅ Extracts Cognito user context from API Gateway authorizer

### 6. Utilities
- ✅ Removed token_utils.py (Cognito handles JWT tokens)
- ✅ Updated error_handler.py for API Gateway response format
- ✅ Removed OAuth error handling (no longer needed)

### 7. Configuration
- ✅ Updated .env.example with Cognito variables
- ✅ Updated setup-local-dynamodb.py (simplified schema)

### 8. Documentation
- ✅ Updated README.md overview and architecture sections
- ✅ Updated design.md overview and architecture diagram
- ✅ Documented authentication flow with Cognito
- ✅ Documented session management (JWT-based)

---

## Remaining Work 🚧

### 1. Documentation Updates

#### README.md
- [ ] Complete deployment section with Cognito setup steps
- [ ] Update testing section for Cognito integration
- [ ] Add Cognito Hosted UI configuration instructions
- [ ] Document OAuth provider setup in Cognito console

#### design.md
- [ ] Remove OAuth Client Manager section (no longer applicable)
- [ ] Remove Session Manager section (Cognito handles sessions)
- [ ] Update correctness properties for Cognito JWT tokens
- [ ] Update Lambda function descriptions (remove OAuth handlers)
- [ ] Update API endpoints section (remove OAuth-specific endpoints)

#### tasks.md
- [ ] Remove Tasks 6-7 (OAuth client manager, session manager)
- [ ] Update Task 5 checkpoint (verify core utilities only)
- [ ] Simplify remaining tasks for Cognito architecture
- [ ] Update task descriptions to reference Cognito instead of custom OAuth
- [ ] Remove property tests related to OAuth and sessions

### 2. Testing
- [ ] Create unit tests for profile_handler.py
- [ ] Create integration tests for Cognito authentication flow
- [ ] Update existing tests to work with Cognito JWT tokens
- [ ] Add tests for CognitoUserContext extraction

### 3. Deployment
- [ ] Test deployment to dev environment
- [ ] Verify Cognito User Pool creation
- [ ] Verify Identity Provider configuration
- [ ] Test OAuth flows with Google and Facebook
- [ ] Verify API Gateway Cognito Authorizer

### 4. Local Development
- [ ] Document Cognito Local setup (or mocking strategy)
- [ ] Create mock Cognito JWT tokens for local testing
- [ ] Update local testing scripts

---

## Key Architecture Changes

### Before (Custom OAuth)
```
Frontend → API Gateway → Lambda (OAuth) → Social Providers
                      → Lambda (Session) → DynamoDB (sessions)
                      → Lambda (Validation) → DynamoDB (sessions)
```

### After (Cognito)
```
Frontend → Cognito (OAuth) → Social Providers
        → API Gateway (Cognito Authorizer) → Lambda (business logic)
                                           → DynamoDB (profiles only)
```

### Eliminated Components
- ❌ OAuth Client Manager (4 Lambda functions)
- ❌ Session Manager (2 Lambda functions)
- ❌ Session storage in DynamoDB
- ❌ Custom session token generation
- ❌ Token validation Lambda
- ❌ OAuth credential management in code

### New Components
- ✅ Cognito User Pool
- ✅ Cognito Identity Providers (Google, Facebook)
- ✅ API Gateway Cognito Authorizer
- ✅ Single UserProfileHandler Lambda

---

## Cost Impact

### Before (Custom OAuth)
- Lambda (OAuth + Session): ~$5/month
- DynamoDB (sessions): ~$1/month
- Secrets Manager (OAuth creds): ~$1/month
- **Total: ~$7/month**

### After (Cognito)
- Cognito User Pools: ~$5-10/month (50 MAU free tier)
- Lambda (business logic only): ~$3/month
- DynamoDB (profiles only): ~$1/month
- **Total: ~$9-14/month**

**Net difference: +$2-7/month, but significantly less code and complexity**

---

## Migration Checklist

### Code Changes
- [x] Update SAM template
- [x] Update data models
- [x] Create profile handler
- [x] Remove obsolete utilities
- [x] Update error handling
- [ ] Update tests

### Documentation
- [x] Update DECISIONS.md
- [x] Update README.md (partial)
- [x] Update design.md (partial)
- [ ] Update tasks.md
- [ ] Complete README.md
- [ ] Complete design.md

### Deployment
- [ ] Deploy to dev environment
- [ ] Test OAuth flows
- [ ] Verify API Gateway authorization
- [ ] Test profile operations

### Testing
- [ ] Unit tests for profile handler
- [ ] Integration tests for Cognito flow
- [ ] Update existing tests
- [ ] Local development testing

---

## Next Steps

1. **Update tasks.md** - Remove OAuth/session tasks, simplify for Cognito
2. **Complete design.md** - Remove OAuth/session sections, update properties
3. **Complete README.md** - Add Cognito deployment and testing instructions
4. **Create tests** - Unit and integration tests for profile handler
5. **Deploy to dev** - Test end-to-end with real Cognito User Pool
6. **Update local dev** - Document Cognito Local or mocking strategy

---

## References

- [DECISIONS.md](./DECISIONS.md) - Decision 12: AWS Cognito for Authentication
- [design.md](./design.md) - Technical design with Cognito architecture
- [template.yaml](../../services/user-management/template.yaml) - SAM template with Cognito resources
- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
