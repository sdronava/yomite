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

For local development, you can:
- Use Cognito Local (community tool)
- Mock Cognito responses in tests
- Deploy to dev environment for integration testing

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

### Deploy to Development

```bash
sam build
sam deploy --config-env dev
```

### Deploy to Staging

```bash
sam build
sam deploy --config-env staging
```

### Deploy to Production

```bash
sam build
sam deploy --config-env prod
```

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Property-based tests
pytest tests/property/

# All tests with coverage
pytest --cov=src --cov-report=term-missing
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
