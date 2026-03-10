---
inclusion: always
---

# Technology Stack

## Core Technologies

### Frontend
- Modern JavaScript/TypeScript framework (React, Vue, or similar)
- Target: Modern browsers, mobile, and tablets
- Modern, immersive UI/UX design

### Backend
- **Language**: Python 3.11+ (ARM64/Graviton2 for cost optimization)
- **API Style**: RESTful API
- **Architecture**: Serverless-first (AWS Lambda)
- **Database**: DynamoDB (single-table design, on-demand billing)
- **API Gateway**: AWS API Gateway HTTP API with Cognito Authorizer
- **Authentication**: AWS Cognito User Pools with social identity providers

### Infrastructure
- **Cloud**: AWS (initial implementation)
- **IaC**: AWS SAM (Serverless Application Model)
- **Compute**: AWS Lambda (Python 3.11, ARM64)
- **Storage**: Amazon DynamoDB
- **Authentication**: AWS Cognito
- **API**: Amazon API Gateway (HTTP API)
- **Monitoring**: CloudWatch Logs, CloudWatch Metrics, AWS X-Ray
- **Local Development**: DynamoDB Local, SAM Local, pytest with moto

## Technology Selection Guidelines

When choosing technologies:
- Prioritize serverless and managed services to minimize operational overhead
- Prioritize well-documented, actively maintained libraries
- Consider security best practices from the start
- Ensure accessibility compliance for user-facing features
- Select tools that support property-based testing where applicable
- Maintain modularity for potential service separation
- Optimize for cost-efficiency (critical for early-stage product)

## Common Commands

### Build
```bash
# Build Lambda function with SAM
cd services/user-management
sam build

# Build with Docker (for ARM64)
sam build --use-container
```

### Test
```bash
# Run all tests
cd services/user-management
pytest

# Run unit tests only
pytest tests/unit/ -v

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_profile_handler.py -v

# Run integration tests (requires DynamoDB Local)
docker-compose up -d
python infrastructure/scripts/setup-local-dynamodb.py
pytest tests/integration/ -v
```

### Development
```bash
# Set up virtual environment
cd services/user-management
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run linting
flake8 src/ tests/ --max-line-length=120

# Format code
black src/ tests/ --line-length=120

# Type checking
mypy src/

# Security scanning
bandit -r src/

# Start DynamoDB Local
docker-compose up -d

# Create local DynamoDB table
python infrastructure/scripts/setup-local-dynamodb.py

# Invoke Lambda locally
sam local invoke UserProfileHandler --event events/get-profile.json

# Start local API
sam local start-api --port 8080
```

### Deployment
```bash
# Deploy to development
cd services/user-management
sam build
sam deploy --config-env dev

# Deploy to staging
sam build
sam deploy --config-env staging

# Deploy to production
sam build
sam deploy --config-env prod

# View logs
sam logs -n UserProfileHandler --stack-name yomite-user-management-dev --tail
```

## Dependencies

### Production Dependencies (requirements.txt)

**Core AWS SDK:**
- `boto3>=1.34.0` - AWS SDK for Python (DynamoDB, Secrets Manager)
- `botocore>=1.34.0` - Low-level AWS service access

**HTTP & API:**
- `requests>=2.31.0` - HTTP library for OAuth and external APIs

**Authentication & Security:**
- `python-jose[cryptography]>=3.3.0` - JWT token handling and validation
- `cryptography>=41.0.0` - Cryptographic operations

**Monitoring & Tracing:**
- `aws-xray-sdk>=2.12.0` - AWS X-Ray tracing for Lambda

**Configuration:**
- `python-dotenv>=1.0.0` - Environment variable management

### Development Dependencies (requirements-dev.txt)

**Testing:**
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Code coverage plugin
- `pytest-mock>=3.12.0` - Mocking utilities
- `hypothesis>=6.92.0` - Property-based testing
- `moto>=4.2.0` - AWS service mocking

**Code Quality:**
- `flake8>=6.1.0` - Linting
- `black>=23.12.0` - Code formatting
- `mypy>=1.7.0` - Static type checking
- `bandit>=1.7.5` - Security vulnerability scanning

**Type Stubs:**
- `boto3-stubs[dynamodb,secretsmanager]>=1.34.0` - Type hints for boto3

### Dependency Management

```bash
# Update dependencies
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements-dev.txt

# Check for security vulnerabilities
pip-audit

# Check for outdated packages
pip list --outdated

# Freeze exact versions (for reproducible builds)
pip freeze > requirements-lock.txt
```

### Security Best Practices

- Review security advisories regularly: https://github.com/advisories
- Use `pip-audit` to scan for known vulnerabilities
- Pin major versions in requirements.txt, use lock file for exact versions
- Update dependencies monthly or when security patches are released
- Test thoroughly after dependency updates
