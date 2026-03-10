# Local Testing Guide

This guide covers strategies for testing the User Registration Service locally without deploying to AWS.

## Overview

The service uses AWS Cognito for authentication, which presents challenges for local testing. This guide provides three approaches with varying levels of complexity and realism.

## Prerequisites

- Python 3.11+ with virtual environment
- Docker (for DynamoDB Local)
- All dependencies installed (`pip install -r requirements-dev.txt`)

## Approach 1: Unit Tests with Mocked Dependencies (Recommended for Development)

This is the fastest and most reliable approach for development and CI/CD.

### Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html --cov-report=term-missing
```

### How It Works

- Uses `unittest.mock` to mock AWS services (DynamoDB, Cognito)
- Uses `moto` library for more realistic AWS mocking
- Tests focus on business logic without external dependencies
- Fast execution (< 1 second for all tests)

### Example: Testing Profile Handler

```python
from unittest.mock import Mock, patch, MagicMock
from handlers.profile_handler import lambda_handler

def test_get_profile():
    # Mock Cognito JWT claims
    event = {
        'requestContext': {
            'http': {'method': 'GET'},
            'authorizer': {
                'jwt': {
                    'claims': {
                        'sub': 'test-user-123',
                        'email': 'test@example.com',
                        'email_verified': 'true',
                        'name': 'Test User'
                    }
                }
            },
            'requestId': 'test-request-id'
        }
    }
    
    # Mock DynamoDB client
    with patch('handlers.profile_handler.get_dynamodb_client') as mock_db:
        mock_db.return_value.get_item.return_value = {
            'PK': 'USER#test-user-123',
            'SK': 'PROFILE',
            'UserId': 'test-user-123',
            'Email': 'test@example.com',
            'Name': 'Test User',
            'Preferences': {'theme': 'dark'},
            'CreatedAt': 1234567890,
            'UpdatedAt': 1234567890
        }
        
        # Execute
        response = lambda_handler(event, Mock(request_id='test-123'))
        
        # Verify
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['data']['email'] == 'test@example.com'
```

### Advantages

- Fast execution
- No external dependencies
- Reliable and deterministic
- Works in CI/CD pipelines
- Easy to test edge cases and error scenarios

### Disadvantages

- Doesn't test actual AWS integration
- Requires maintaining mocks

## Approach 2: Integration Tests with DynamoDB Local

This approach tests against a real DynamoDB instance running locally, but still mocks Cognito.

### Setup

```bash
# Start DynamoDB Local
docker-compose up -d

# Create local table
python infrastructure/scripts/setup-local-dynamodb.py

# Set environment variables
export DYNAMODB_TABLE_NAME=yomite-user-data-local
export DYNAMODB_ENDPOINT_URL=http://localhost:8000
export AWS_REGION=us-east-1

# Run integration tests
pytest tests/integration/ -v
```

### Example: Integration Test

```python
import boto3
import os
from handlers.profile_handler import lambda_handler

def test_profile_lifecycle():
    # Setup: Create DynamoDB client
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='us-east-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    table = dynamodb.Table('yomite-user-data-local')
    
    # Mock Cognito event
    event = {
        'requestContext': {
            'http': {'method': 'GET'},
            'authorizer': {
                'jwt': {
                    'claims': {
                        'sub': 'integration-test-user',
                        'email': 'integration@example.com',
                        'email_verified': 'true',
                        'name': 'Integration Test User'
                    }
                }
            },
            'requestId': 'integration-test-id'
        }
    }
    
    # Test: GET profile (should auto-create)
    response = lambda_handler(event, Mock(request_id='test-123'))
    assert response['statusCode'] == 200
    
    # Verify: Check DynamoDB
    item = table.get_item(
        Key={'PK': 'USER#integration-test-user', 'SK': 'PROFILE'}
    )
    assert item['Item']['Email'] == 'integration@example.com'
    
    # Test: PUT profile (update)
    event['requestContext']['http']['method'] = 'PUT'
    event['body'] = json.dumps({'name': 'Updated Name', 'preferences': {'theme': 'dark'}})
    
    response = lambda_handler(event, Mock(request_id='test-123'))
    assert response['statusCode'] == 200
    
    # Verify: Check updated data
    item = table.get_item(
        Key={'PK': 'USER#integration-test-user', 'SK': 'PROFILE'}
    )
    assert item['Item']['Name'] == 'Updated Name'
    assert item['Item']['Preferences']['theme'] == 'dark'
    
    # Cleanup
    table.delete_item(Key={'PK': 'USER#integration-test-user', 'SK': 'PROFILE'})
```

### Advantages

- Tests real DynamoDB operations
- Catches DynamoDB-specific issues (schema, queries, etc.)
- More realistic than pure mocking

### Disadvantages

- Requires Docker
- Slower than unit tests
- Still mocks Cognito

## Approach 3: Mock JWT Tokens for Manual Testing

This approach allows manual testing of the Lambda function with mock JWT tokens.

### Creating Mock JWT Tokens

You can create mock JWT tokens using [jwt.io](https://jwt.io) or Python:

```python
import jwt
import time

# Create mock JWT token
payload = {
    'sub': 'test-user-123',
    'email': 'test@example.com',
    'email_verified': 'true',
    'name': 'Test User',
    'cognito:username': 'test-user-123',
    'iss': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX',
    'aud': 'your-client-id',
    'exp': int(time.time()) + 3600,  # Expires in 1 hour
    'iat': int(time.time()),
    'token_use': 'access'
}

# Note: For local testing, signature verification is typically disabled
# In production, API Gateway validates the signature
token = jwt.encode(payload, 'secret', algorithm='HS256')
print(f"Mock JWT Token: {token}")
```

### Testing with SAM Local

```bash
# Create event file with mock JWT
cat > events/get-profile-local.json << EOF
{
  "requestContext": {
    "http": {
      "method": "GET"
    },
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
    "requestId": "local-test-request"
  }
}
EOF

# Invoke Lambda locally
sam local invoke UserProfileHandler \
  --event events/get-profile-local.json \
  --env-vars env-local.json

# Start local API
sam local start-api --port 8080 --env-vars env-local.json
```

### Environment Variables (env-local.json)

```json
{
  "UserProfileHandler": {
    "DYNAMODB_TABLE_NAME": "yomite-user-data-local",
    "DYNAMODB_ENDPOINT_URL": "http://host.docker.internal:8000",
    "AWS_REGION": "us-east-1",
    "ENVIRONMENT": "local",
    "LOG_LEVEL": "DEBUG"
  }
}
```

### Testing with curl

```bash
# Start local API
sam local start-api --port 8080 --env-vars env-local.json

# Test GET profile (mock JWT in event, not in Authorization header)
# Note: SAM Local doesn't validate JWT signatures
curl http://localhost:8080/profile
```

### Advantages

- Tests Lambda function in SAM Local environment
- Can test API Gateway integration locally
- Good for debugging

### Disadvantages

- Doesn't validate JWT signatures (API Gateway does this in production)
- Requires SAM CLI
- Slower than unit tests

## Approach 4: Testing Against Real Cognito (Dev Environment)

For the most realistic testing, deploy to a dev environment and use real Cognito.

### Setup

```bash
# Deploy to dev
sam build && sam deploy --config-env dev

# Get Cognito Hosted UI URL
aws cloudformation describe-stacks \
  --stack-name yomite-user-management-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolDomain`].OutputValue' \
  --output text
```

### Testing Flow

1. Open Cognito Hosted UI in browser
2. Authenticate with Google or Facebook
3. Copy JWT token from browser (Developer Tools → Network → Headers)
4. Use token to test API endpoints

```bash
# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name yomite-user-management-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Test with real JWT token
curl -H "Authorization: Bearer YOUR_REAL_JWT_TOKEN" \
  ${API_ENDPOINT}/profile
```

### Advantages

- Tests complete authentication flow
- Validates JWT signature verification
- Tests real AWS integration
- Most realistic testing

### Disadvantages

- Requires AWS deployment
- Slower feedback loop
- Costs money (minimal with free tier)

## Recommended Testing Strategy

Use a combination of approaches:

1. **Development**: Unit tests with mocks (Approach 1)
   - Fast feedback
   - Test business logic
   - Test error handling

2. **Pre-commit**: Integration tests with DynamoDB Local (Approach 2)
   - Validate DynamoDB operations
   - Catch schema issues

3. **CI/CD**: Automated unit + integration tests
   - Run on every commit
   - Block merges if tests fail

4. **Pre-deployment**: Manual testing with SAM Local (Approach 3)
   - Debug complex issues
   - Test Lambda configuration

5. **Post-deployment**: E2E tests against dev environment (Approach 4)
   - Validate complete flow
   - Test with real Cognito

## Troubleshooting

### DynamoDB Local Connection Issues

```bash
# Check if DynamoDB Local is running
docker ps | grep dynamodb

# Check logs
docker logs yomite-dynamodb-local

# Restart if needed
docker-compose restart dynamodb-local
```

### SAM Local Issues

```bash
# Check Docker is running
docker info

# Use --debug flag for verbose output
sam local invoke UserProfileHandler \
  --event events/get-profile-local.json \
  --debug

# Check Lambda logs
# SAM Local outputs logs to console
```

### Import Path Issues

```bash
# Ensure PYTHONPATH includes src directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or use pytest with proper configuration (pytest.ini)
pytest tests/unit/ -v
```

## Best Practices

1. **Write unit tests first** - Fast feedback, easy to maintain
2. **Use integration tests for critical paths** - Validate DynamoDB operations
3. **Mock external dependencies** - Don't test AWS services, test your code
4. **Use fixtures for common test data** - DRY principle
5. **Test error scenarios** - Invalid input, missing data, DynamoDB errors
6. **Use descriptive test names** - `test_get_profile_creates_new_user_from_cognito_data`
7. **Keep tests independent** - No shared state between tests
8. **Clean up test data** - Delete test records after integration tests

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [moto documentation](http://docs.getmoto.org/)
- [AWS SAM Local documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local.html)
- [DynamoDB Local documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html)
