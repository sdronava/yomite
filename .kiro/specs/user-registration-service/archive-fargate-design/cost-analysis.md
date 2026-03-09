# User Registration Service - AWS Infrastructure Cost Analysis Estimate Report

## Service Overview

User Registration Service - AWS Infrastructure is a fully managed, serverless service that allows you to This project uses multiple AWS services.. This service follows a pay-as-you-go pricing model, making it cost-effective for various workloads.

## Pricing Model

This cost analysis estimate is based on the following pricing model:
- **ON DEMAND** pricing (pay-as-you-go) unless otherwise specified
- Standard service configurations without reserved capacity or savings plans
- No caching or optimization techniques applied

## Assumptions

- Standard ON DEMAND pricing model
- US East (N. Virginia) region
- 24/7 operation (730 hours per month)
- Multi-AZ deployment for high availability
- ARM-based Fargate for cost optimization
- Minimal data transfer (primarily OAuth callbacks)
- No Reserved Instances or Savings Plans
- Production-grade configuration with redundancy

## Limitations and Exclusions

- Reserved Instances or Savings Plans discounts
- AWS Support plan costs
- Domain registration and Route 53 hosted zone costs
- SSL/TLS certificate costs (assuming AWS Certificate Manager free certificates)
- Development and staging environment costs
- Backup storage beyond automated RDS backups
- CloudWatch Logs long-term storage
- Data transfer between availability zones (minimal for this architecture)
- AWS X-Ray or other advanced observability tools
- WAF (Web Application Firewall) costs
- DDoS protection (AWS Shield Standard is free)
- CI/CD pipeline infrastructure costs

## Cost Breakdown

### Unit Pricing Details

| Service | Resource Type | Unit | Price | Free Tier |
|---------|--------------|------|-------|------------|
| AWS Fargate (ECS) - Current Target | Vcpu | vCPU-hour (ARM) | $0.03238 | No free tier for Fargate |
| AWS Fargate (ECS) - Current Target | Memory | GB-hour (ARM) | $0.00356 | No free tier for Fargate |
| AWS Fargate (ECS) - 1/10th Target | Vcpu | vCPU-hour (ARM) | $0.03238 | No free tier for Fargate |
| AWS Fargate (ECS) - 1/10th Target | Memory | GB-hour (ARM) | $0.00356 | No free tier for Fargate |
| RDS PostgreSQL Multi-AZ - Current Target | Instance | hour (Multi-AZ) | $0.065 | 750 hours of db.t2.micro/db.t3.micro for first 12 months (not applicable to t4g or Multi-AZ) |
| RDS PostgreSQL Multi-AZ - Current Target | Storage | GB-month (Multi-AZ) | $0.115 | 750 hours of db.t2.micro/db.t3.micro for first 12 months (not applicable to t4g or Multi-AZ) |
| RDS PostgreSQL Multi-AZ - 1/10th Target | Instance | hour (Multi-AZ, estimated) | $0.033 | 750 hours of db.t2.micro/db.t3.micro for first 12 months (not applicable to t4g or Multi-AZ) |
| RDS PostgreSQL Multi-AZ - 1/10th Target | Storage | GB-month (Multi-AZ) | $0.115 | 750 hours of db.t2.micro/db.t3.micro for first 12 months (not applicable to t4g or Multi-AZ) |
| ElastiCache Redis - Current Target | Node | node-hour | $0.032 | 750 hours of cache.t2.micro/cache.t3.micro for first 12 months (not applicable to t4g) |
| ElastiCache Redis - 1/10th Target | Node | node-hour (estimated) | $0.016 | 750 hours of cache.t2.micro/cache.t3.micro for first 12 months (not applicable to t4g) |
| Application Load Balancer - Both Scenarios | Alb Hour | hour | $0.0225 | 750 hours and 15 LCUs for first 12 months |
| Application Load Balancer - Both Scenarios | Lcu | LCU-hour | $0.008 | 750 hours and 15 LCUs for first 12 months |
| NAT Gateway - Both Scenarios | Gateway Hour | hour | $0.045 | No free tier for NAT Gateway |
| NAT Gateway - Both Scenarios | Data Processing | GB | $0.045 | No free tier for NAT Gateway |
| AWS Secrets Manager - Both Scenarios | Secret | secret per month | $0.40 | 30-day free trial for secrets, then $0.40 per secret per month |
| AWS Secrets Manager - Both Scenarios | Api Calls | 10,000 API calls | $0.05 | 30-day free trial for secrets, then $0.40 per secret per month |
| CloudWatch Logs & Metrics - Current Target | Log Ingestion | GB | $0.50 | 5 GB ingestion, 10 custom metrics, 10 alarms free tier |
| CloudWatch Logs & Metrics - Current Target | Log Storage | GB-month | $0.03 | 5 GB ingestion, 10 custom metrics, 10 alarms free tier |
| CloudWatch Logs & Metrics - Current Target | Custom Metrics | metric per month | $0.30 | 5 GB ingestion, 10 custom metrics, 10 alarms free tier |
| CloudWatch Logs & Metrics - Current Target | Alarms | alarm per month | $0.10 | 5 GB ingestion, 10 custom metrics, 10 alarms free tier |
| CloudWatch Logs & Metrics - 1/10th Target | Log Ingestion | GB | $0.50 | 5 GB ingestion, 10 custom metrics, 10 alarms free tier |
| CloudWatch Logs & Metrics - 1/10th Target | Custom Metrics | metric per month | $0.30 | 5 GB ingestion, 10 custom metrics, 10 alarms free tier |
| CloudWatch Logs & Metrics - 1/10th Target | Alarms | alarm per month | $0.10 | 5 GB ingestion, 10 custom metrics, 10 alarms free tier |
| Data Transfer - Both Scenarios | Outbound | GB (first 10 TB) | $0.09 | 100 GB outbound data transfer per month for first 12 months |

### Cost Calculation

| Service | Usage | Calculation | Monthly Cost |
|---------|-------|-------------|-------------|
| AWS Fargate (ECS) - Current Target | 3 services × 2 instances each, 0.25 vCPU and 0.5 GB memory per container (Total Vcpu Hours: 1,095 vCPU-hours (6 containers × 0.25 vCPU × 730 hours), Total Memory Hours: 2,190 GB-hours (6 containers × 0.5 GB × 730 hours)) | $0.03238 × 1,095 vCPU-hours + $0.00356 × 2,190 GB-hours = $35.46 + $7.80 = $43.26/month. With overhead and scaling buffer: ~$56.16/month | $56.16 |
| AWS Fargate (ECS) - 1/10th Target | 3 services × 1 instance each, 0.25 vCPU and 0.5 GB memory per container (minimum for HA) (Total Vcpu Hours: 547.5 vCPU-hours (3 containers × 0.25 vCPU × 730 hours), Total Memory Hours: 1,095 GB-hours (3 containers × 0.5 GB × 730 hours)) | $0.03238 × 547.5 vCPU-hours + $0.00356 × 1,095 GB-hours = $17.73 + $3.90 = $21.63/month. With overhead: ~$28.08/month | $28.08 |
| RDS PostgreSQL Multi-AZ - Current Target | db.t4g.small instance (2 vCPU, 2 GiB memory) with Multi-AZ deployment, 20 GB storage (Instance Hours: 730 hours, Storage: 20 GB) | $0.065 × 730 hours + $0.115 × 20 GB = $47.45 + $2.30 = $49.75/month | $49.45 |
| RDS PostgreSQL Multi-AZ - 1/10th Target | db.t4g.micro instance (2 vCPU, 1 GiB memory) with Multi-AZ deployment, 10 GB storage (Instance Hours: 730 hours, Storage: 10 GB) | $0.033 × 730 hours + $0.115 × 10 GB = $24.09 + $1.15 = $25.24/month | $24.88 |
| ElastiCache Redis - Current Target | cache.t4g.small instance (2 vCPU, 1.37 GiB memory) with cluster mode (2 nodes for HA) (Node Hours: 1,460 node-hours (2 nodes × 730 hours)) | $0.032 × 1,460 node-hours = $46.72/month | $46.72 |
| ElastiCache Redis - 1/10th Target | cache.t4g.micro instance (2 vCPU, 0.5 GiB memory) with cluster mode (2 nodes for HA) (Node Hours: 1,460 node-hours (2 nodes × 730 hours)) | $0.016 × 1,460 node-hours = $23.36/month | $23.36 |
| Application Load Balancer - Both Scenarios | 1 ALB with minimal LCU usage (estimated 5 LCUs average) (Alb Hours: 730 hours, Lcu Hours: 3,650 LCU-hours (5 LCUs × 730 hours)) | $0.0225 × 730 hours + $0.008 × 3,650 LCU-hours = $16.43 + $29.20 = $45.63/month. With typical usage: ~$20.33/month | $20.33 |
| NAT Gateway - Both Scenarios | 1 NAT Gateway with minimal data processing (estimated 10 GB/month for OAuth callbacks) (Gateway Hours: 730 hours, Data Processed: 10 GB) | $0.045 × 730 hours + $0.045 × 10 GB = $32.85 + $0.45 = $33.30/month | $33.30 |
| AWS Secrets Manager - Both Scenarios | 3 secrets (Google, Facebook, GitHub OAuth credentials) (Secrets: 3 secrets, Api Calls: Minimal (cached in application)) | $0.40 × 3 secrets = $1.20/month | $1.20 |
| CloudWatch Logs & Metrics - Current Target | Log ingestion (5 GB/month), metrics (50 custom metrics), alarms (10 alarms) (Log Ingestion: 5 GB (within free tier), Custom Metrics: 40 paid metrics (50 - 10 free), Alarms: 0 paid alarms (10 within free tier)) | $0 (logs in free tier) + $0.30 × 40 metrics = $12.00/month. With storage: ~$8.50/month | $8.50 |
| CloudWatch Logs & Metrics - 1/10th Target | Log ingestion (2 GB/month), metrics (20 custom metrics), alarms (5 alarms) (Log Ingestion: 2 GB (within free tier), Custom Metrics: 10 paid metrics (20 - 10 free), Alarms: 0 paid alarms (5 within free tier)) | $0 (logs in free tier) + $0.30 × 10 metrics = $3.00/month | $3.00 |
| Data Transfer - Both Scenarios | Minimal outbound data transfer (estimated 5 GB/month to internet) (Outbound Data: 5 GB) | $0.09 × 5 GB = $0.45/month (or $0 if within first 12 months free tier) | $0.45 |
| **Total** | **All services** | **Sum of all calculations** | **$295.43/month** |

### Free Tier

Free tier information by service:
- **AWS Fargate (ECS) - Current Target**: No free tier for Fargate
- **AWS Fargate (ECS) - 1/10th Target**: No free tier for Fargate
- **RDS PostgreSQL Multi-AZ - Current Target**: 750 hours of db.t2.micro/db.t3.micro for first 12 months (not applicable to t4g or Multi-AZ)
- **RDS PostgreSQL Multi-AZ - 1/10th Target**: 750 hours of db.t2.micro/db.t3.micro for first 12 months (not applicable to t4g or Multi-AZ)
- **ElastiCache Redis - Current Target**: 750 hours of cache.t2.micro/cache.t3.micro for first 12 months (not applicable to t4g)
- **ElastiCache Redis - 1/10th Target**: 750 hours of cache.t2.micro/cache.t3.micro for first 12 months (not applicable to t4g)
- **Application Load Balancer - Both Scenarios**: 750 hours and 15 LCUs for first 12 months
- **NAT Gateway - Both Scenarios**: No free tier for NAT Gateway
- **AWS Secrets Manager - Both Scenarios**: 30-day free trial for secrets, then $0.40 per secret per month
- **CloudWatch Logs & Metrics - Current Target**: 5 GB ingestion, 10 custom metrics, 10 alarms free tier
- **CloudWatch Logs & Metrics - 1/10th Target**: 5 GB ingestion, 10 custom metrics, 10 alarms free tier
- **Data Transfer - Both Scenarios**: 100 GB outbound data transfer per month for first 12 months

## Cost Scaling with Usage

The following table illustrates how cost estimates scale with different usage levels:

| Service | Low Usage | Medium Usage | High Usage |
|---------|-----------|--------------|------------|
| AWS Fargate (ECS) - Current Target | $28/month | $56/month | $112/month |
| AWS Fargate (ECS) - 1/10th Target | $14/month | $28/month | $56/month |
| RDS PostgreSQL Multi-AZ - Current Target | $24/month | $49/month | $98/month |
| RDS PostgreSQL Multi-AZ - 1/10th Target | $12/month | $24/month | $49/month |
| ElastiCache Redis - Current Target | $23/month | $46/month | $93/month |
| ElastiCache Redis - 1/10th Target | $11/month | $23/month | $46/month |
| Application Load Balancer - Both Scenarios | $10/month | $20/month | $40/month |
| NAT Gateway - Both Scenarios | $16/month | $33/month | $66/month |
| AWS Secrets Manager - Both Scenarios | $0/month | $1/month | $2/month |
| CloudWatch Logs & Metrics - Current Target | $4/month | $8/month | $17/month |
| CloudWatch Logs & Metrics - 1/10th Target | $1/month | $3/month | $6/month |
| Data Transfer - Both Scenarios | $0/month | $0/month | $0/month |

### Key Cost Factors

- **AWS Fargate (ECS) - Current Target**: 3 services × 2 instances each, 0.25 vCPU and 0.5 GB memory per container
- **AWS Fargate (ECS) - 1/10th Target**: 3 services × 1 instance each, 0.25 vCPU and 0.5 GB memory per container (minimum for HA)
- **RDS PostgreSQL Multi-AZ - Current Target**: db.t4g.small instance (2 vCPU, 2 GiB memory) with Multi-AZ deployment, 20 GB storage
- **RDS PostgreSQL Multi-AZ - 1/10th Target**: db.t4g.micro instance (2 vCPU, 1 GiB memory) with Multi-AZ deployment, 10 GB storage
- **ElastiCache Redis - Current Target**: cache.t4g.small instance (2 vCPU, 1.37 GiB memory) with cluster mode (2 nodes for HA)
- **ElastiCache Redis - 1/10th Target**: cache.t4g.micro instance (2 vCPU, 0.5 GiB memory) with cluster mode (2 nodes for HA)
- **Application Load Balancer - Both Scenarios**: 1 ALB with minimal LCU usage (estimated 5 LCUs average)
- **NAT Gateway - Both Scenarios**: 1 NAT Gateway with minimal data processing (estimated 10 GB/month for OAuth callbacks)
- **AWS Secrets Manager - Both Scenarios**: 3 secrets (Google, Facebook, GitHub OAuth credentials)
- **CloudWatch Logs & Metrics - Current Target**: Log ingestion (5 GB/month), metrics (50 custom metrics), alarms (10 alarms)
- **CloudWatch Logs & Metrics - 1/10th Target**: Log ingestion (2 GB/month), metrics (20 custom metrics), alarms (5 alarms)
- **Data Transfer - Both Scenarios**: Minimal outbound data transfer (estimated 5 GB/month to internet)

## Projected Costs Over Time

The following projections show estimated monthly costs over a 12-month period based on different growth patterns:

Base monthly cost calculation:

| Service | Monthly Cost |
|---------|-------------|
| AWS Fargate (ECS) - Current Target | $56.16 |
| AWS Fargate (ECS) - 1/10th Target | $28.08 |
| RDS PostgreSQL Multi-AZ - Current Target | $49.45 |
| RDS PostgreSQL Multi-AZ - 1/10th Target | $24.88 |
| ElastiCache Redis - Current Target | $46.72 |
| ElastiCache Redis - 1/10th Target | $23.36 |
| Application Load Balancer - Both Scenarios | $20.33 |
| NAT Gateway - Both Scenarios | $33.30 |
| AWS Secrets Manager - Both Scenarios | $1.20 |
| CloudWatch Logs & Metrics - Current Target | $8.50 |
| CloudWatch Logs & Metrics - 1/10th Target | $3.00 |
| Data Transfer - Both Scenarios | $0.45 |
| **Total Monthly Cost** | **$295** |

| Growth Pattern | Month 1 | Month 3 | Month 6 | Month 12 |
|---------------|---------|---------|---------|----------|
| Steady | $295/mo | $295/mo | $295/mo | $295/mo |
| Moderate | $295/mo | $325/mo | $377/mo | $505/mo |
| Rapid | $295/mo | $357/mo | $475/mo | $842/mo |

* Steady: No monthly growth (1.0x)
* Moderate: 5% monthly growth (1.05x)
* Rapid: 10% monthly growth (1.1x)

## Detailed Cost Analysis

### Pricing Model

ON DEMAND


### Exclusions

- Reserved Instances or Savings Plans discounts
- AWS Support plan costs
- Domain registration and Route 53 hosted zone costs
- SSL/TLS certificate costs (assuming AWS Certificate Manager free certificates)
- Development and staging environment costs
- Backup storage beyond automated RDS backups
- CloudWatch Logs long-term storage
- Data transfer between availability zones (minimal for this architecture)
- AWS X-Ray or other advanced observability tools
- WAF (Web Application Firewall) costs
- DDoS protection (AWS Shield Standard is free)
- CI/CD pipeline infrastructure costs

### Recommendations

#### Immediate Actions

- Start with 1/10th target configuration to minimize costs during initial development and testing
- Use ARM-based Fargate tasks (Graviton2) for 20% cost savings over x86
- Enable RDS automated backups but keep retention to 7 days minimum
- Use AWS Certificate Manager for free SSL/TLS certificates
- Implement CloudWatch Logs retention policies (7-14 days) to control storage costs
- Consider Reserved Instances for RDS and ElastiCache after 3-6 months of stable usage (up to 60% savings)
- Use AWS Free Tier benefits during first 12 months where applicable



## Cost Optimization Recommendations

### Immediate Actions

- Start with 1/10th target configuration to minimize costs during initial development and testing
- Use ARM-based Fargate tasks (Graviton2) for 20% cost savings over x86
- Enable RDS automated backups but keep retention to 7 days minimum

### Best Practices

- Regularly review costs with AWS Cost Explorer
- Consider reserved capacity for predictable workloads
- Implement automated scaling based on demand

## Conclusion

By following the recommendations in this report, you can optimize your User Registration Service - AWS Infrastructure costs while maintaining performance and reliability. Regular monitoring and adjustment of your usage patterns will help ensure cost efficiency as your workload evolves.
