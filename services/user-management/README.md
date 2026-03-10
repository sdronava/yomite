# User Registration Service

Serverless user registration and authentication service for Yomite using AWS Cognito, Lambda, and DynamoDB.

## Features

- Social login (Google, Facebook) via AWS Cognito
- Managed authentication with JWT tokens
- User profile management
- Automatic token validation via API Gateway
- Secure, scalable, and cost-effective

## Architecture

- **Authentication**: AWS Cognito User Pools
- **Compute**: AWS Lambda (Python 3.11, ARM64)
- **Database**: DynamoDB (user profiles and app data)
- **API**: API Gateway with Cognito Authorizer
- **IaC**: AWS SAM

## Key Benefits

- **No custom OAuth code** - Cognito handles social login flows
- **Automatic token validation** - API Gateway validates JWTs
- **Stateless sessions** - JWT tokens, no server-side storage
- **Cost-effective** - ~$15-25/month for current target
- **Secure** - Industry-standard JWT, managed by AWS

## Project Structure

```
services/user-management/
├── src/
│   ├── handlers/          # Lambda function handlers
│   ├── services/          # Business logic (profile management)
│   ├── models/            # Data models (CognitoUserContext, UserProfile)
│   └── utils/             # Utilities (logging, validation, DynamoDB)
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── property/          # Property-based tests
├── infrastructure/
│   └── scripts/           # Setup and deployment scripts
├── template.yaml          # AWS SAM template (Cognito + Lambda + DynamoDB)
└── requirements.txt       # Python dependencies
```

## Prerequisites

- Python 3.11+
- AWS CLI configured
- AWS SAM CLI
- AWS Account with Cognito access
- OAuth credentials from Google and Facebook

## Local Development Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure OAuth Providers

Create OAuth applications:
- **Google**: https://console.cloud.google.com/apis/credentials
- **Facebook**: https://developers.facebook.com/apps

Store credentials in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name yomite/oauth/google \
  --secret-string '{"client_id":"YOUR_GOOGLE_CLIENT_ID","client_secret":"YOUR_GOOGLE_CLIENT_SECRET"}'

aws secretsmanager create-secret \
  --name yomite/oauth/facebook \
  --secret-string '{"client_id":"YOUR_FACEBOOK_APP_ID","client_secret":"YOUR_FACEBOOK_APP_SECRET"}'
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/unit/ -v
```

### 5. Local Testing with Cognito

For local development, you have several options:

**Option 1: Use Real Cognito User Pool (Recommended)**
- Deploy to dev environment
- Use real Cognito User Pool for local testing
- Frontend can use Cognito SDK to authenticate
- Copy JWT tokens from browser for API testing

**Option 2: Mock Cognito JWT Tokens**
- Create mock JWT tokens for local testing
- Use tools like [jwt.io](https://jwt.io) to generate test tokens
- Include required claims: `sub`, `email`, `email_verified`

**Example Mock JWT Claims:**
```json
{
  "sub": "test-user-123",
  "email": "test@example.com",
  "email_verified": "true",
  "name": "Test User",
  "cognito:username": "test-user-123",
  "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX",
  "aud": "your-client-id",
  "exp": 1234567890
}
```

**Option 3: Use Cognito Local (Community Tool)**
- [cognito-local](https://github.com/jagregory/cognito-local) - Local Cognito emulator
- Requires additional setup and configuration
- Not officially supported by AWS

**Testing Profile Handler Locally:**
```bash
# Start DynamoDB Local
docker-compose up -d

# Create local table
python infrastructure/scripts/setup-local-dynamodb.py

# Invoke Lambda locally with SAM
sam local invoke UserProfileHandler \
  --event events/get-profile.json \
  --env-vars env.json

# Start local API
sam local start-api --port 8080
```

**Example Event (events/get-profile.json):**
```json
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
    "requestId": "test-request-id"
  }
}
```

## API Endpoints

### Authentication (Handled by Cognito)
- Cognito Hosted UI: `https://{domain}.auth.{region}.amazoncognito.com/login`
- OAuth callback: Configured in Cognito User Pool Client

### Application APIs (Require JWT token)
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile

All API requests must include JWT Access Token:
```
Authorization: Bearer {access_token}
```

## Deployment

### Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed (`pip install aws-sam-cli`)
- AWS Account with permissions for:
  - Cognito User Pools
  - Lambda
  - DynamoDB
  - API Gateway
  - CloudWatch Logs
  - IAM roles

### Step 1: Configure OAuth Providers

Before deploying, you need to create OAuth applications with Google and Facebook:

**Google OAuth Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new OAuth 2.0 Client ID
3. Set authorized redirect URIs:
   - Dev: `https://yomite-dev-{account-id}.auth.{region}.amazoncognito.com/oauth2/idpresponse`
   - Prod: `https://yomite-prod-{account-id}.auth.{region}.amazoncognito.com/oauth2/idpresponse`
4. Note the Client ID and Client Secret

**Facebook OAuth Setup:**
1. Go to [Facebook Developers](https://developers.facebook.com/apps)
2. Create a new app and add Facebook Login product
3. Set Valid OAuth Redirect URIs (same pattern as Google)
4. Note the App ID and App Secret

### Step 2: Store OAuth Credentials in AWS Secrets Manager

```bash
# Google OAuth credentials
aws secretsmanager create-secret \
  --name yomite/oauth/google \
  --secret-string '{"client_id":"YOUR_GOOGLE_CLIENT_ID","client_secret":"YOUR_GOOGLE_CLIENT_SECRET"}' \
  --region us-east-1

# Facebook OAuth credentials
aws secretsmanager create-secret \
  --name yomite/oauth/facebook \
  --secret-string '{"client_id":"YOUR_FACEBOOK_APP_ID","client_secret":"YOUR_FACEBOOK_APP_SECRET"}' \
  --region us-east-1
```

### Step 3: Build and Deploy

**Deploy to Development:**
```bash
cd services/user-management

# Build Lambda function
sam build

# Deploy to dev environment
sam deploy --config-env dev --guided

# Follow prompts:
# - Stack Name: yomite-user-management-dev
# - AWS Region: us-east-1
# - Parameter Environment: dev
# - Confirm changes before deploy: Y
# - Allow SAM CLI IAM role creation: Y
# - Save arguments to configuration file: Y
```

**Deploy to Staging:**
```bash
sam build
sam deploy --config-env staging
```

**Deploy to Production:**
```bash
sam build
sam deploy --config-env prod
```

### Step 4: Verify Deployment

After deployment, SAM will output:
- `ApiEndpoint` - API Gateway URL
- `UserPoolId` - Cognito User Pool ID
- `UserPoolClientId` - Cognito User Pool Client ID
- `UserPoolDomain` - Cognito Hosted UI domain

Test the deployment:
```bash
# Get Cognito Hosted UI URL
COGNITO_DOMAIN=$(aws cloudformation describe-stacks \
  --stack-name yomite-user-management-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolDomain`].OutputValue' \
  --output text)

echo "Cognito Hosted UI: https://${COGNITO_DOMAIN}/login"

# Test profile endpoint (requires JWT token)
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name yomite-user-management-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  ${API_ENDPOINT}/profile
```

### Troubleshooting Deployment

**Issue: Cognito Identity Provider creation fails**
- Verify OAuth secrets exist in Secrets Manager
- Check secret names match exactly: `yomite/oauth/google`, `yomite/oauth/facebook`
- Verify secret format is correct JSON with `client_id` and `client_secret` keys

**Issue: API Gateway returns 401 Unauthorized**
- Verify JWT token is valid and not expired
- Check Cognito User Pool Client ID matches the audience in JWT
- Verify API Gateway Cognito Authorizer is configured correctly

**Issue: Lambda function errors**
- Check CloudWatch Logs: `/aws/lambda/user-profile-handler-{env}`
- Verify DynamoDB table exists and Lambda has permissions
- Check environment variables are set correctly

## Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Integration Tests

```bash
# Run integration tests (requires DynamoDB Local)
docker-compose up -d
python infrastructure/scripts/setup-local-dynamodb.py
pytest tests/integration/ -v
```

### Testing with Mock Cognito

```python
# Example: Mock Cognito JWT claims in tests
def test_get_profile_with_mock_cognito():
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
    
    response = lambda_handler(event, MockContext())
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['success'] is True
    assert body['data']['email'] == 'test@example.com'
```

### End-to-End Testing

```bash
# Deploy to dev environment
sam build && sam deploy --config-env dev

# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name yomite-user-management-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Authenticate via Cognito Hosted UI (manual step)
# Copy JWT token from browser

# Test profile endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  ${API_ENDPOINT}/profile

# Test profile update
curl -X PUT \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Name","preferences":{"theme":"dark"}}' \
  ${API_ENDPOINT}/profile
```

## Monitoring

- CloudWatch Logs: `/aws/lambda/user-*-handler-{env}`
- CloudWatch Metrics: Lambda invocations, errors, duration
- X-Ray Tracing: Enabled for all Lambda functions

## Cost Estimate

- **Cognito**: ~$5-10/month (50 MAU free tier, then $0.0055/MAU)
- **Lambda**: ~$3-5/month (1M requests free tier)
- **DynamoDB**: ~$1-2/month (25 GB free tier)
- **API Gateway**: ~$3-5/month (1M requests free tier)
- **Total**: ~$15-25/month (with free tier benefits)

## Documentation

- [Design Document](../../.kiro/specs/user-registration-service/design.md)
- [Requirements](../../.kiro/specs/user-registration-service/requirements.md)
- [Architecture Decisions](../../.kiro/specs/user-registration-service/DECISIONS.md)
- [Quick Start Guide](../../.kiro/specs/user-registration-service/QUICK-START.md)

## Security Notes

- **JWT Storage**: Tokens stored client-side (XSS mitigation TODO)
- **Token Validation**: Automatic via API Gateway Cognito Authorizer
- **HTTPS**: Enforced by API Gateway
- **Rate Limiting**: Configured in API Gateway

## License

Proprietary - Yomite
