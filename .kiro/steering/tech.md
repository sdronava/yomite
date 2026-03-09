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
- **Language**: Python 3
- RESTful or GraphQL API
- **Architecture**: Serverless-first (AWS Lambda)
- **Database**: DynamoDB (single-table design)
- **API Gateway**: AWS API Gateway with Lambda integration

### Infrastructure
- **Cloud**: Cloud-agnostic design, AWS for initial implementation
- **IaC**: AWS CDK or CloudFormation
- **Serverless**: AWS Lambda, DynamoDB, API Gateway
- **Local Development**: Full local testing capability required (LocalStack, SAM Local, or similar)

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

As the project evolves, document common commands here:

### Build
```bash
# To be defined based on chosen build system
```

### Test
```bash
# To be defined based on chosen test framework
```

### Development
```bash
# To be defined based on chosen development workflow
```

## Dependencies

No dependencies currently installed. When adding dependencies:
- Document the purpose of each major dependency
- Keep dependencies up to date
- Review security advisories regularly
