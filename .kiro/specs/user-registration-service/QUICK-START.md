# Quick Start Guide: Serverless User Registration Service

## Overview

This guide helps you quickly set up and deploy the serverless User Registration Service.

## Prerequisites

```bash
# Install Python 3.11+
python --version

# Install AWS SAM CLI
pip install aws-sam-cli

# Install Docker
docker --version

# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure
```

## Local Development Setup

### 1. Start Local DynamoDB

```bash
# Start DynamoDB Local with Docker
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local

# Create local table
aws dynamodb create-table \
    --table-name yomite-user-registration-local \
    --attribute-definitions \
        AttributeName=PK,AttributeType=S \
        AttributeName=SK,AttributeType=S \
        AttributeName=Email,AttributeType=S \
        AttributeName=EmailProviderKey,AttributeType=S \
    --key-schema \
        AttributeName=PK,KeyType=HASH \
        AttributeName=SK,KeyType=RANGE \
    --global-secondary-indexes \
        "[{\"IndexName\":\"EmailIndex\",\"KeySchema\":[{\"AttributeName\":\"Email\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"SK\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}},{\"IndexName\":\"EmailProviderIndex\",\"KeySchema\":[{\"AttributeName\":\"EmailProviderKey\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"SK\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000 \
    --region us-east-1
```

### 2. Start Local API

```bash
# Build Lambda functions
sam build

# Start local API Gateway + Lambda
sam local start-api --port 3000 --env-vars env.json
```

### 3. Test Endpoints

```bash
# Test registration
curl -X POST http://localhost:3000/auth/register/google \
  -H "Content-Type: application/json" \
  -d '{"redirect_uri": "http://localhost:3000/callback"}'

# Test validation
curl -X GET http://localhost:3000/auth/validate \
  -H "Authorization: Bearer v1.abc123..."
```

## Running Tests

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run property-based tests
pytest tests/property/ -v --hypothesis-show-statistics
```

## Deployment

### Deploy to Dev

```bash
# Build
sam build

# Deploy
sam deploy --config-env dev --guided
```

### Deploy to Staging

```bash
sam deploy --config-env staging
```

### Deploy to Production

```bash
sam deploy --config-env prod
```

## Common Commands

### View Logs

```bash
# Tail logs for a function
sam logs -n RegistrationHandler --stack-name user-registration-service-dev --tail

# View recent logs
sam logs -n RegistrationHandler --stack-name user-registration-service-dev --start-time '10min ago'
```

### Invoke Function Locally

```bash
# Invoke with test event
sam local invoke RegistrationHandler --event events/register.json
```

### Delete Stack

```bash
# Delete dev stack
aws cloudformation delete-stack --stack-name user-registration-service-dev
```

## Environment Variables

Create `env.json` for local development:

```json
{
  "RegistrationHandler": {
    "DYNAMODB_TABLE_NAME": "yomite-user-registration-local",
    "ENVIRONMENT": "local",
    "LOG_LEVEL": "DEBUG",
    "AWS_ENDPOINT_URL": "http://host.docker.internal:8000"
  },
  "AuthenticationHandler": {
    "DYNAMODB_TABLE_NAME": "yomite-user-registration-local",
    "ENVIRONMENT": "local",
    "LOG_LEVEL": "DEBUG",
    "AWS_ENDPOINT_URL": "http://host.docker.internal:8000"
  }
}
```

## Monitoring

### View CloudWatch Dashboard

```bash
# Get dashboard URL
aws cloudwatch get-dashboard \
    --dashboard-name user-registration-service-prod
```

### Check Costs

```bash
# View current month costs
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --filter file://cost-filter.json
```

## Troubleshooting

### Cold Starts

If validation latency is high:
1. Check provisioned concurrency is enabled
2. Increase provisioned concurrency instances
3. Monitor CloudWatch metrics

### DynamoDB Throttling

If seeing throttling errors:
1. Check consumed capacity in CloudWatch
2. Switch to provisioned capacity with auto-scaling
3. Increase provisioned capacity

### Lambda Timeouts

If functions are timing out:
1. Check CloudWatch Logs for errors
2. Increase timeout in template.yaml
3. Optimize code for performance

### High Costs

If costs are higher than expected:
1. Check CloudWatch Logs retention (reduce if needed)
2. Review Lambda memory allocation (reduce if over-provisioned)
3. Check DynamoDB capacity mode (switch to on-demand if low traffic)
4. Review provisioned concurrency (reduce if not needed)

## Key Metrics to Monitor

- Lambda invocations and errors
- Lambda duration (p50, p95, p99)
- DynamoDB consumed capacity
- API Gateway 4xx and 5xx errors
- CloudWatch Logs ingestion
- Monthly costs

## Cost Targets

- **Current Target:** <$25/month
- **With Free Tier:** <$10/month (first year)
- **10x Growth:** <$100/month

## Support

For issues or questions:
1. Check CloudWatch Logs
2. Review design document
3. Check AWS service health dashboard
4. Contact team lead

## Quick Reference

| Task | Command |
|------|---------|
| Build | `sam build` |
| Deploy Dev | `sam deploy --config-env dev` |
| Deploy Prod | `sam deploy --config-env prod` |
| View Logs | `sam logs -n FunctionName --tail` |
| Run Tests | `pytest` |
| Local API | `sam local start-api` |
| Invoke Local | `sam local invoke FunctionName` |

