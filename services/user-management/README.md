# User Registration Service

Serverless user registration and authentication service for Yomite using AWS Lambda, DynamoDB, and API Gateway.

## Features

- Social login (Google, Facebook, GitHub)
- Account linking for multiple providers
- Secure session management with token-based authentication
- Rate limiting and input validation
- Property-based testing for correctness validation

## Architecture

- **Compute**: AWS Lambda (Python 3.11, ARM64)
- **Database**: DynamoDB (single-table design)
- **API**: API Gateway (HTTP API)
- **IaC**: AWS SAM

## Project Structure

```
services/user-management/
├── src/
│   ├── handlers/          # Lambda function handlers
│   ├── services/          # Business logic
│   ├── models/            # Data models
│   └── utils/             # Utilities
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── property/          # Property-based tests
├── infrastructure/
│   └── scripts/           # Setup and deployment scripts
├── template.yaml          # AWS SAM template
└── requirements.txt       # Python dependencies
```

## Prerequisites

- Python 3.11+
- AWS CLI configured
- AWS SAM CLI
- Docker (for local DynamoDB)

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

### 2. Start Local DynamoDB

```bash
# Start DynamoDB Local with Docker Compose
docker-compose up -d

# Create local table
python infrastructure/scripts/setup-local-dynamodb.py
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local configuration
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run property-based tests
pytest tests/property/ -v
```

### 5. Start Local API

```bash
# Build Lambda functions
sam build

# Start local API Gateway
sam local start-api --env-vars .env
```

The API will be available at `http://localhost:3000`

## API Endpoints

- `POST /auth/register/{provider}` - Register with social provider
- `POST /auth/login/{provider}` - Login with social provider
- `POST /auth/logout` - Logout and invalidate session
- `GET /auth/validate` - Validate session token

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

- **Development**: ~$10/month (with Free Tier)
- **Current Target**: ~$23/month
- **10x Growth**: ~$80-100/month

## Documentation

- [Design Document](../../.kiro/specs/user-registration-service/design.md)
- [Requirements](../../.kiro/specs/user-registration-service/requirements.md)
- [Architecture Decisions](../../.kiro/specs/user-registration-service/DECISIONS.md)
- [Quick Start Guide](../../.kiro/specs/user-registration-service/QUICK-START.md)

## License

Proprietary - Yomite
