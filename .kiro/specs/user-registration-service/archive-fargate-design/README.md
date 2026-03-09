# Fargate-Based Design Archive

This folder contains the original Fargate-based design for the User Registration Service.

## Why Archived?

The project switched to a serverless architecture (AWS Lambda + DynamoDB) for the following reasons:

1. **Cost Optimization**: 89% cost savings (~$23/month vs ~$220/month)
2. **Operational Simplicity**: Automatic scaling, no infrastructure management
3. **Early-Stage Fit**: Better suited for variable traffic and budget constraints
4. **No Feature Compromise**: All 26 correctness properties maintained

## Contents

- `cost-analysis.md` - Detailed cost breakdown for Fargate design
- `best-practices-review.md` - Best practices review and recommendations
- `SUMMARY.md` - Summary of Fargate design
- `tasks.md` - Implementation tasks for Fargate design

## Fargate Design Overview

**Architecture**: ECS Fargate + RDS PostgreSQL + ElastiCache Redis + ALB

**Key Components**:
- 3 Fargate services (Registration, Authentication, Session Manager)
- RDS PostgreSQL Multi-AZ for user data
- ElastiCache Redis for session storage
- Application Load Balancer for routing
- VPC with NAT Gateway

**When to Consider Fargate**:
- Traffic consistently >500 RPS
- Need complex SQL queries and JOINs
- Cannot tolerate cold starts
- Vendor lock-in concerns
- Cost per request becomes competitive at scale

## Migration Path

If the project needs to migrate back to Fargate:

1. Review this archived design
2. Update for current requirements
3. Create migration plan from DynamoDB to PostgreSQL
4. Implement dual-write strategy during transition
5. Gradually shift traffic to Fargate services

## Reference

See `COMPARISON.md` in the parent directory for detailed comparison between Fargate and Serverless designs.
