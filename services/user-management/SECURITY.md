# Security

## Known Vulnerabilities

### CVE-2024-23342 (ecdsa 0.19.1)

**Status**: Accepted Risk

**Description**: python-ecdsa is subject to a Minerva timing attack on the P-256 curve. The vulnerability affects ECDSA signatures, key generation, and ECDH operations.

**Mitigation**:
- This is a transitive dependency from `python-jose[cryptography]`
- We do not use ecdsa directly for signing operations
- AWS Cognito handles all JWT signing and verification
- The python-ecdsa project considers side-channel attacks out of scope
- No fix is planned by the maintainers

**Risk Assessment**: Low
- We don't perform ECDSA signing operations in our code
- JWT validation is handled by API Gateway Cognito Authorizer
- Attack requires precise timing measurements and multiple signature samples

**Action**: Monitor for updates to python-jose that may switch to a different ECDSA library

## Security Scanning

We use the following tools for security scanning:

### Dependency Vulnerability Scanning

```bash
# Scan for known vulnerabilities
pip-audit

# Scan with detailed descriptions
pip-audit --desc

# Generate report
pip-audit --format json > security-report.json
```

### Static Application Security Testing (SAST)

```bash
# Scan for security issues in code
bandit -r src/

# Generate report
bandit -r src/ -f json -o bandit-report.json
```

### Secrets Detection

```bash
# Initialize secrets baseline
detect-secrets scan > .secrets.baseline

# Audit detected secrets
detect-secrets audit .secrets.baseline

# Scan for new secrets
detect-secrets scan --baseline .secrets.baseline
```

## Security Best Practices

### Code Security

1. **Input Validation**: All user inputs are validated and sanitized
2. **SQL Injection**: Not applicable (using DynamoDB with parameterized queries)
3. **XSS Prevention**: API returns JSON only, frontend must sanitize
4. **CSRF Protection**: JWT tokens in Authorization header (not cookies)
5. **Sensitive Data**: Logged data is sanitized to remove tokens and secrets

### Infrastructure Security

1. **Authentication**: AWS Cognito with OAuth 2.0
2. **Authorization**: API Gateway Cognito Authorizer validates JWT
3. **Encryption in Transit**: HTTPS enforced by API Gateway
4. **Encryption at Rest**: DynamoDB encryption enabled
5. **Least Privilege**: Lambda IAM roles have minimal permissions

### Secrets Management

1. **OAuth Credentials**: Stored in AWS Secrets Manager
2. **Environment Variables**: No secrets in environment variables
3. **Code Repository**: No secrets committed to git
4. **Local Development**: Use .env file (gitignored)

### Monitoring and Incident Response

1. **Logging**: Structured JSON logs to CloudWatch
2. **Tracing**: AWS X-Ray for distributed tracing
3. **Alerting**: CloudWatch Alarms for errors and anomalies
4. **Audit Trail**: CloudWatch Logs retention (30 days production)

## Reporting Security Issues

If you discover a security vulnerability, please email security@yomite.com with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

Do not create public GitHub issues for security vulnerabilities.

## Security Updates

- Dependencies are reviewed monthly
- Security patches are applied within 7 days of disclosure
- Critical vulnerabilities are patched within 24 hours

## Compliance

- GDPR: User data can be deleted on request
- CCPA: User data can be exported on request
- SOC 2: Planned for future (not currently compliant)
