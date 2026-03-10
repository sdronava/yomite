# Local Testing with Cognito

This guide explains how to test the User Management service locally with Cognito authentication.

## Overview

The User Management service uses AWS Cognito for authentication. For local development and testing, you have several options:

1. **Use Real Cognito User Pool** (Recommended for integration testing)
2. **Mock Cognito JWT Tokens** (Recommended for unit/integration tests)
3. **Use Cognito Local** (Community tool, not officially supported)

## Option 1: Use Real Cognito User Pool (Recommended)

This approach uses a real Cognito User Pool deployed in AWS for local testing.

### Prerequisites

- AWS account with Cognito access
- OAuth credentials from Google and Facebook
- AWS CLI configured

### Setup Steps

1. **Deploy to dev environment:**
   ```bash
   cd services/user-management
   sam build
   sam deploy --config-env dev --guided
   ```

2. **Get Cognito User Pool details:**
   ```bash
   aws cloudformation describe-stacks \
     --stack-name yomite-user-registration-dev \
     --query 'Stacks[0].Outputs' \
     --output table
   ```

3. **Test authentication via Cognito Hosted UI:**
   - Open the Cognito Hosted UI URL from stack outputs
   - Sign in with Google or Facebook
   - Copy the JWT token from the browser (check URL parameters or use browser dev tools)

4. **Test Lambda locally with real JWT:**
   ```bash
   # Create test event with real JWT claims
   cat > events/get-profile-real.json << EOF
   {
     "requestContext": {
       "http": {"method": "GET"},
       "authorizer": {
         "jwt": {
           "claims": {
             "sub": "YOUR_USER_SUB",
             "email": "your-email@example.com",
             "email_verified": "true",
             "name": "Your Name"
           }
         }
       },
       "requestId": "test-request-id"
     }
   }
   EOF

   # Invoke Lambda locally
   sam local invoke UserProfileHandler --event events/get-profile-real.json
   ```

5. **Test API locally:**
   ```bash
   # Start local API
   sam local start-api --port 8080

   # Test with real JWT token
   curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8080/profile
   ```

## Option 2: Mock Cognito JWT Tokens (Recommended for Tests)

This approach creates mock JWT tokens for testing without requiring a real Cognito User Pool.

### Creating Mock JWT Tokens

1. **Use jwt.io to create test tokens:**
   - Go to https://jwt.io
   - Create a JWT with required claims:
     ```json
     {
       "sub": "test-user-123",
       "email": "test@example.com",
       "email_verified": "true",
       "name": "Test User",
       "picture": "https://example.com/picture.jpg",
       "cognito:username": "test-user-123",
       "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX",
       "aud": "your-client-id",
       "exp": 9999999999
     }
     ```

2. **Use in test events:**
   ```json
   {
     "requestContext": {
       "http": {"method": "GET"},
       "authorizer": {
         "jwt": {
           "claims": {
             "sub": "test-user-123",
             "email": "test@example.com",
             "email_verified": "true",
             "name": "Test User"
           }
         }
       },
       "requestId": "test-request-id"
     }
   }
   ```

### Integration Tests with Mock Cognito

The integration tests use moto to mock AWS services and provide mock Cognito claims:

```python
# Example from tests/integration/test_profile_integration.py
def test_get_profile_creates_new_profile(dynamodb_table, cognito_event):
    """Test GET /profile creates a new profile from Cognito data."""
    response = lambda_handler(cognito_event, MockContext())
    
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["data"]["email"] == "test@example.com"
```

### Running Integration Tests

```bash
# Start DynamoDB Local
docker-compose up -d

# Create local table
python infrastructure/scripts/setup-local-dynamodb.py

# Run integration tests
pytest tests/integration/ -v
```

## Option 3: Cognito Local (Community Tool)

[cognito-local](https://github.com/jagregory/cognito-local) is a community-maintained local Cognito emulator.

### Setup

1. **Install cognito-local:**
   ```bash
   npm install -g cognito-local
   ```

2. **Start cognito-local:**
   ```bash
   cognito-local
   ```

3. **Configure your application:**
   - Point Cognito endpoints to `http://localhost:9229`
   - Create test users and user pools

**Note:** This is not officially supported by AWS and may not have full feature parity with real Cognito.

## Testing Profile Handler Locally

### Test GET /profile

```bash
# Create test event
cat > events/get-profile.json << EOF
{
  "requestContext": {
    "http": {"method": "GET"},
    "authorizer": {
      "jwt": {
        "claims": {
          "sub": "test-user-123",
          "email": "test@example.com",
          "email_verified": "true",
          "name": "Test User"
        }
      }
    },
    "requestId": "test-request-id"
  }
}
EOF

# Invoke Lambda
sam local invoke UserProfileHandler --event events/get-profile.json
```

### Test PUT /profile

```bash
# Create test event
cat > events/update-profile.json << EOF
{
  "requestContext": {
    "http": {"method": "PUT"},
    "authorizer": {
      "jwt": {
        "claims": {
          "sub": "test-user-123",
          "email": "test@example.com",
          "email_verified": "true",
          "name": "Test User"
        }
      }
    },
    "requestId": "test-request-id"
  },
  "body": "{\"name\":\"Updated Name\",\"preferences\":{\"theme\":\"dark\"}}"
}
EOF

# Invoke Lambda
sam local invoke UserProfileHandler --event events/update-profile.json
```

### Test with SAM Local API

```bash
# Start local API
sam local start-api --port 8080

# Test GET /profile (mock JWT in event)
curl http://localhost:8080/profile

# Test PUT /profile (mock JWT in event)
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Name","preferences":{"theme":"dark"}}' \
  http://localhost:8080/profile
```

**Note:** SAM Local API doesn't validate JWT tokens by default. For full JWT validation, deploy to AWS and test against the real API Gateway.

## Troubleshooting

### Issue: Lambda can't connect to DynamoDB Local

**Solution:** Ensure DynamoDB Local is running and accessible:
```bash
docker-compose up -d
curl http://localhost:8000/
```

### Issue: Missing Cognito claims in event

**Solution:** Ensure your test event includes the `requestContext.authorizer.jwt.claims` structure:
```json
{
  "requestContext": {
    "authorizer": {
      "jwt": {
        "claims": {
          "sub": "user-id",
          "email": "user@example.com"
        }
      }
    }
  }
}
```

### Issue: Integration tests fail with DynamoDB errors

**Solution:** Create the local table before running tests:
```bash
python infrastructure/scripts/setup-local-dynamodb.py
```

## Best Practices

1. **Use mock Cognito claims for unit/integration tests** - Fast and reliable
2. **Use real Cognito for end-to-end testing** - Validates full authentication flow
3. **Keep test JWT tokens in version control** - Makes tests reproducible
4. **Document required JWT claims** - Helps other developers understand requirements
5. **Test both success and error cases** - Missing claims, invalid tokens, etc.

## Additional Resources

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [SAM Local Testing](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-invoke.html)
- [JWT.io](https://jwt.io) - JWT token debugger
- [cognito-local](https://github.com/jagregory/cognito-local) - Community Cognito emulator
