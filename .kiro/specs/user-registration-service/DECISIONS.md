# Architecture Decision Record

This document captures key architectural and technical decisions made during the design of the User Registration Service.

## Decision 1: Serverless Architecture over Container-Based (Fargate)

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Early-stage product with no users and no funding
- Cost is a critical constraint
- Traffic patterns are unpredictable and variable
- Small team with limited DevOps resources
- Well-defined access patterns for user registration and authentication

**Decision:**
Adopt serverless architecture using AWS Lambda + DynamoDB + API Gateway instead of ECS Fargate + RDS PostgreSQL + ElastiCache Redis.

**Rationale:**
1. **Cost Optimization (Primary Driver):**
   - Serverless: ~$23/month for current target capacity
   - Fargate: ~$220/month for current target capacity
   - 89% cost savings critical for unfunded early-stage product
   - Pay-per-use model eliminates idle capacity costs
   - AWS Free Tier provides 1M Lambda requests and 25 GB DynamoDB storage

2. **Operational Simplicity:**
   - Automatic scaling without configuration
   - No infrastructure management (patching, updates)
   - Reduced operational overhead for small team
   - Faster deployment and iteration cycles

3. **Access Pattern Fit:**
   - User registration has well-defined query patterns
   - No complex JOINs or ad-hoc queries needed
   - DynamoDB single-table design supports all required access patterns
   - Session management fits naturally with DynamoDB TTL

4. **Scalability:**
   - Automatic scaling from 0 to 10,000+ RPS
   - No pre-provisioning required
   - Scales independently per function

**Consequences:**

*Positive:*
- Significant cost savings enable longer runway
- Faster time to market (6 weeks vs 8 weeks)
- Automatic scaling handles traffic spikes
- Lower operational burden

*Negative:*
- Cold start latency (400-1200ms) for infrequent operations
- DynamoDB query patterns require upfront design
- Vendor lock-in to AWS services
- Harder to debug (no SSH access to containers)

*Mitigations:*
- Provisioned concurrency for validation-handler (high frequency)
- Careful DynamoDB schema design with GSIs
- Fargate design archived for future migration if needed
- Comprehensive CloudWatch logging for debugging

**Alternatives Considered:**
1. **ECS Fargate + RDS + Redis:** More flexible but 89% more expensive
2. **Hybrid Approach:** Complexity not justified at current scale
3. **Self-Hosted on EC2:** Even more operational overhead

**Review Trigger:**
- Traffic consistently exceeds 500 RPS
- Cold starts become problematic for user experience
- Need complex queries not supported by DynamoDB
- Cost per request becomes competitive with Fargate at scale

---

## Decision 2: DynamoDB Single-Table Design

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Need to store users, social identities, and sessions
- Cost optimization is critical
- Access patterns are well-defined
- No complex relational queries required

**Decision:**
Use a single DynamoDB table with composite keys and Global Secondary Indexes (GSIs) instead of multiple tables or RDS PostgreSQL.

**Rationale:**
1. **Cost Efficiency:**
   - Single table reduces provisioned capacity costs
   - Fewer GSIs needed compared to multiple tables
   - ~$1.13/month vs $49/month for RDS Multi-AZ

2. **Performance:**
   - Single-digit millisecond latency
   - Consistent performance at scale
   - No connection pooling overhead

3. **Access Pattern Support:**
   - All required queries supported with PK/SK and 2 GSIs
   - EmailIndex for registration lookups
   - EmailProviderIndex for login lookups
   - No JOINs needed for user registration domain

4. **Session Management:**
   - DynamoDB TTL automatically deletes expired sessions
   - No manual cleanup jobs needed
   - Eliminates need for separate Redis cache

**Consequences:**

*Positive:*
- Significant cost savings
- Automatic session cleanup with TTL
- Fast, predictable performance
- Simplified data model

*Negative:*
- Less flexible than SQL for ad-hoc queries
- Schema changes require careful planning
- Learning curve for single-table design patterns
- Cannot easily add complex queries later

*Mitigations:*
- Comprehensive access pattern analysis upfront
- GSIs provide query flexibility
- Can add more GSIs if needed (with cost consideration)
- Fargate + PostgreSQL design archived for migration path

**Alternatives Considered:**
1. **Multiple DynamoDB Tables:** Higher cost, more complex
2. **RDS PostgreSQL:** 43x more expensive, overkill for simple queries
3. **Aurora Serverless:** Still 10x more expensive than DynamoDB

---

## Decision 3: Provisioned Concurrency for Validation Handler Only

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Session validation is high-frequency operation (100K+ requests/day)
- Other operations (registration, login) are infrequent
- Cold starts acceptable for infrequent operations
- Cost optimization is critical

**Decision:**
Enable provisioned concurrency (2 instances) for validation-handler only. Use on-demand for registration-handler, authentication-handler, and session-handler.

**Rationale:**
1. **Cost-Performance Balance:**
   - Provisioned concurrency costs $5.16/month for 2 instances
   - Eliminates cold starts for 90% of requests (validation)
   - Registration/login cold starts acceptable (1-2 second operations anyway)

2. **User Experience:**
   - Validation must be fast (<50ms) for good UX
   - Registration/login already take 1-2 seconds (OAuth flow)
   - Additional 400-1200ms cold start negligible for infrequent operations

3. **Traffic Patterns:**
   - Validation: 100K requests/day (high frequency)
   - Authentication: 10K requests/day (medium frequency)
   - Registration: 1K requests/day (low frequency)
   - Logout: <1K requests/day (low frequency)

**Consequences:**

*Positive:*
- Fast validation for authenticated requests
- Minimal cost increase ($5.16/month)
- Cold starts only affect infrequent operations

*Negative:*
- Occasional cold starts for registration/login
- Additional cost for provisioned concurrency

*Mitigations:*
- Monitor cold start metrics in CloudWatch
- Can increase provisioned concurrency if needed
- Can add provisioned concurrency to other functions if traffic increases

**Alternatives Considered:**
1. **Provisioned Concurrency for All Functions:** 4x cost increase
2. **No Provisioned Concurrency:** Poor validation latency
3. **VPC Warm-up Strategy:** Complex, not needed

---

## Decision 4: API Gateway over Application Load Balancer

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Need HTTP API for frontend clients
- Serverless architecture chosen
- Rate limiting and CORS required
- Cost optimization is critical

**Decision:**
Use AWS API Gateway (HTTP API) instead of Application Load Balancer.

**Rationale:**
1. **Native Lambda Integration:**
   - Direct Lambda invocation without VPC
   - Automatic request/response transformation
   - Built-in authorization and validation

2. **Cost Efficiency:**
   - API Gateway: ~$6.62/month for current target
   - ALB: ~$20/month (always-on cost)
   - 67% cost savings

3. **Built-in Features:**
   - Rate limiting and throttling
   - CORS configuration
   - Request validation
   - API key management
   - CloudWatch integration

4. **Serverless Fit:**
   - No VPC required (simplified networking)
   - Scales automatically with Lambda
   - Pay-per-request pricing model

**Consequences:**

*Positive:*
- Lower cost than ALB
- Simplified architecture (no VPC)
- Built-in rate limiting and CORS
- Automatic scaling

*Negative:*
- Less flexible than ALB for complex routing
- API Gateway-specific configuration
- 29-second timeout limit (acceptable for our use case)

*Mitigations:*
- All operations complete in <30 seconds
- Can migrate to ALB if complex routing needed
- API Gateway features sufficient for current requirements

**Alternatives Considered:**
1. **Application Load Balancer:** More expensive, requires VPC
2. **API Gateway REST API:** More expensive than HTTP API
3. **Direct Lambda Function URLs:** No rate limiting or API management

---

## Decision 5: Python 3 for Lambda Functions

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Backend language selection for Lambda functions
- Team familiarity and ecosystem considerations
- Performance and cold start requirements
- Property-based testing with Hypothesis

**Decision:**
Use Python 3.11+ for all Lambda functions.

**Rationale:**
1. **Ecosystem and Libraries:**
   - Rich ecosystem for OAuth clients (requests-oauthlib, authlib)
   - Excellent AWS SDK (boto3) support
   - Hypothesis for property-based testing
   - Strong typing with type hints

2. **Development Velocity:**
   - Rapid development and iteration
   - Extensive documentation and community support
   - Easy to write and maintain
   - Good local testing support (pytest, moto)

3. **Cold Start Performance:**
   - Python cold starts: 400-800ms (acceptable)
   - Faster than Java/C# (1-2 seconds)
   - Comparable to Node.js
   - Provisioned concurrency eliminates cold starts for critical functions

4. **Team Alignment:**
   - Consistent with backend technology choice
   - Single language for all backend services
   - Easier to share code and patterns

**Consequences:**

*Positive:*
- Fast development cycles
- Rich library ecosystem
- Good testing support
- Team familiarity

*Negative:*
- Slower cold starts than Go/Rust
- Higher memory usage than compiled languages
- Runtime overhead vs compiled languages

*Mitigations:*
- Provisioned concurrency for high-frequency functions
- Optimize package size (layer for dependencies)
- Use Python 3.11+ for performance improvements

**Alternatives Considered:**
1. **Node.js:** Similar cold starts, less familiar to team
2. **Go:** Faster cold starts but steeper learning curve
3. **Java:** Much slower cold starts (1-2 seconds)

---

## Decision 6: AWS SAM for Infrastructure as Code

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Need Infrastructure as Code for serverless deployment
- Team wants cloud-agnostic design with AWS implementation
- Local development and testing required
- Deployment automation needed

**Decision:**
Use AWS SAM (Serverless Application Model) for infrastructure definition and deployment.

**Rationale:**
1. **Serverless-First:**
   - Purpose-built for serverless applications
   - Simplified Lambda + API Gateway + DynamoDB definitions
   - Less verbose than CloudFormation
   - Built on CloudFormation (can extend if needed)

2. **Local Development:**
   - SAM Local for local Lambda testing
   - Local API Gateway simulation
   - DynamoDB Local integration
   - Matches production behavior

3. **Deployment Simplicity:**
   - Single command deployment (sam deploy)
   - Built-in packaging and upload
   - Environment-specific configurations
   - Rollback support

4. **AWS Integration:**
   - Native CloudFormation integration
   - CloudWatch Logs integration
   - IAM role management
   - Secrets Manager integration

**Consequences:**

*Positive:*
- Fast local development cycle
- Simple deployment process
- Good documentation and examples
- Active community support

*Negative:*
- AWS-specific (not cloud-agnostic)
- Less flexible than CDK for complex infrastructure
- Learning curve for SAM-specific syntax

*Mitigations:*
- Can migrate to CDK if complexity increases
- SAM templates are CloudFormation (portable)
- Document infrastructure decisions for future migration

**Alternatives Considered:**
1. **AWS CDK:** More flexible but more complex, overkill for current needs
2. **Terraform:** Cloud-agnostic but less serverless-optimized
3. **Serverless Framework:** Third-party dependency, less AWS-native

---

## Decision 7: No VPC for Lambda Functions

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Lambda functions need to access DynamoDB, Secrets Manager, and external OAuth providers
- VPC adds complexity and cost (NAT Gateway)
- Security and network isolation considerations

**Decision:**
Deploy Lambda functions without VPC. Use IAM roles and AWS service endpoints for security.

**Rationale:**
1. **Cost Savings:**
   - No NAT Gateway required ($33/month savings)
   - No VPC endpoints needed
   - Simplified networking

2. **Performance:**
   - No VPC cold start penalty (additional 5-10 seconds)
   - Direct internet access for OAuth providers
   - Faster DynamoDB access (no VPC routing)

3. **Security:**
   - IAM roles provide access control
   - DynamoDB encryption at rest
   - Secrets Manager for OAuth credentials
   - HTTPS for all external communication
   - API Gateway handles rate limiting

4. **Simplicity:**
   - No subnet management
   - No security group configuration
   - No NAT Gateway maintenance
   - Easier to debug and troubleshoot

**Consequences:**

*Positive:*
- $33/month cost savings
- Faster cold starts
- Simpler architecture
- Easier to manage

*Negative:*
- Lambda functions have internet access
- Cannot access VPC-only resources (not needed currently)
- Less network isolation

*Mitigations:*
- IAM roles restrict access to specific resources
- CloudWatch Logs for audit trail
- API Gateway rate limiting prevents abuse
- Can add VPC later if needed (e.g., for RDS access)

**Alternatives Considered:**
1. **VPC with NAT Gateway:** $33/month more expensive, slower cold starts
2. **VPC with VPC Endpoints:** Complex, not needed for current requirements

---

## Decision 8: Session Token Format and Storage

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Need secure session tokens for authenticated requests
- Token must be cryptographically secure (256-bit entropy)
- Token must be validated quickly (<50ms)
- Session data must be stored durably

**Decision:**
Use versioned base64url-encoded tokens (format: `v1.{random_string}`) stored in DynamoDB with SHA-256 hash as partition key.

**Rationale:**
1. **Security:**
   - 256-bit entropy (secrets.token_bytes(32))
   - Cryptographically secure random generation
   - SHA-256 hash prevents token enumeration
   - Version prefix enables future token format changes

2. **Performance:**
   - DynamoDB lookup by hash is fast (<10ms)
   - No token decryption needed
   - Stateless validation (no shared state)

3. **Storage Efficiency:**
   - Hash as partition key (fixed size)
   - TTL for automatic cleanup
   - No separate session store needed

4. **Flexibility:**
   - Version prefix (v1.) allows format evolution
   - Can add JWT later if needed
   - Can rotate token format without breaking existing tokens

**Consequences:**

*Positive:*
- Fast validation (<10ms DynamoDB lookup)
- Secure token generation
- Automatic session cleanup with TTL
- Future-proof with versioning

*Negative:*
- Tokens are opaque (cannot decode without DB lookup)
- Requires DynamoDB query for every validation
- Cannot validate offline

*Mitigations:*
- Provisioned concurrency keeps validation fast
- DynamoDB is highly available (99.99% SLA)
- Can add JWT later if offline validation needed

**Alternatives Considered:**
1. **JWT Tokens:** Larger size, no automatic expiration, harder to revoke
2. **UUID Tokens:** No versioning, less entropy
3. **Encrypted Tokens:** Slower validation, key management complexity

---

## Decision 9: Account Linking Strategy

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Users may register with multiple social providers using same email
- Need to handle duplicate email scenarios gracefully
- User experience should be seamless

**Decision:**
Automatically link accounts when a user registers with a different provider using an email that already exists in the system.

**Rationale:**
1. **User Experience:**
   - Seamless account linking without user intervention
   - Single account per email address
   - Users can login with any linked provider

2. **Data Integrity:**
   - Email uniqueness enforced
   - No duplicate accounts
   - Clear account ownership

3. **Security:**
   - Email verified by social provider
   - OAuth flow ensures user owns the email
   - User notified of account linking

4. **Flexibility:**
   - Users can link multiple providers
   - Can login with any linked provider
   - Can unlink providers later (future feature)

**Consequences:**

*Positive:*
- Better user experience
- No duplicate accounts
- Flexible authentication options

*Negative:*
- Potential security concern if email is compromised
- User might not expect automatic linking
- Cannot have separate accounts with same email

*Mitigations:*
- Clear notification when accounts are linked
- Social providers verify email ownership
- Can add email verification later if needed
- Audit log of account linking events

**Alternatives Considered:**
1. **Reject Duplicate Emails:** Poor user experience
2. **Manual Account Linking:** Complex user flow
3. **Separate Accounts per Provider:** Data fragmentation

---

## Decision 10: Property-Based Testing with Hypothesis

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Need to validate 26 correctness properties
- Traditional unit tests may miss edge cases
- Want to ensure system behaves correctly across input space

**Decision:**
Use Hypothesis for property-based testing of all 26 correctness properties.

**Rationale:**
1. **Comprehensive Testing:**
   - Generates thousands of test cases automatically
   - Finds edge cases humans might miss
   - Tests properties across entire input space

2. **Correctness Validation:**
   - Each property maps to specific requirements
   - Properties define expected behavior formally
   - Failures indicate requirement violations

3. **Regression Prevention:**
   - Hypothesis shrinks failing examples
   - Minimal failing case aids debugging
   - Can replay specific failing cases

4. **Python Ecosystem:**
   - Native Python library (no external dependencies)
   - Integrates with pytest
   - Good documentation and community

**Consequences:**

*Positive:*
- Higher confidence in correctness
- Finds edge cases early
- Documents expected behavior formally
- Prevents regressions

*Negative:*
- Longer test execution time
- Learning curve for property-based testing
- May find issues in test setup (false positives)

*Mitigations:*
- Run property tests in CI/CD pipeline
- Use @example decorator for known edge cases
- Configure max_examples based on CI time budget
- Document property test patterns for team

**Alternatives Considered:**
1. **Unit Tests Only:** May miss edge cases
2. **QuickCheck (Haskell):** Wrong language
3. **fast-check (JavaScript):** Wrong language

---

## Decision 11: Monorepo with Service Isolation

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Multiple sub-projects planned (User Management, future reading features)
- Want flexibility to separate services into independent repos later
- Need to maintain modularity and clear boundaries
- Single repo simplifies initial development and coordination

**Decision:**
Implement services in isolated subdirectories within a monorepo structure, with each service self-contained and ready for future extraction.

**Project Structure:**
```
yomite/                          # Monorepo root
├── services/
│   ├── user-management/         # User Registration Service
│   │   ├── src/                # Lambda functions, services, models
│   │   ├── tests/              # Unit and property-based tests
│   │   ├── infrastructure/     # SAM template, scripts
│   │   ├── template.yaml       # AWS SAM template
│   │   ├── requirements.txt    # Python dependencies
│   │   ├── README.md           # Service documentation
│   │   └── .gitignore          # Service-specific ignores
│   └── [future-services]/      # Other services
├── frontend/                    # Frontend application
├── .kiro/
│   ├── specs/                  # Feature specifications
│   └── steering/               # AI guidance documents
└── README.md                    # Project overview
```

**Rationale:**
1. **Service Isolation:**
   - Each service has its own src/, tests/, infrastructure/
   - Independent dependencies (requirements.txt per service)
   - Self-contained deployment (template.yaml per service)
   - Clear boundaries enable future extraction

2. **Monorepo Benefits (Current):**
   - Simplified coordination during initial development
   - Shared tooling and CI/CD configuration
   - Easier cross-service refactoring
   - Single git history for project evolution

3. **Future Flexibility:**
   - Each service can be extracted to its own repo
   - Minimal changes needed (move folder, update paths)
   - Independent versioning and deployment
   - Can use git subtree or git filter-branch for extraction

4. **Alignment with Architecture:**
   - Matches modular architecture from steering documents
   - Supports eventual microservices separation
   - Maintains cloud-agnostic design principles

**Consequences:**

*Positive:*
- Clear service boundaries from day one
- Easy to extract services later
- Simplified initial development
- Shared infrastructure and tooling

*Negative:*
- Slightly more complex directory structure
- Need to manage per-service dependencies
- CI/CD must handle multiple services

*Mitigations:*
- Document service structure in README
- Use consistent patterns across services
- Automate multi-service CI/CD with GitHub Actions
- Keep shared utilities minimal (avoid tight coupling)

**Service Extraction Process (Future):**
When ready to extract a service:
1. Create new repository
2. Use `git subtree split` or `git filter-branch` to extract service history
3. Update import paths and dependencies
4. Set up independent CI/CD
5. Update documentation and references

**Alternatives Considered:**
1. **Flat Structure:** All code in root - harder to separate later
2. **Separate Repos from Start:** Premature, adds coordination overhead
3. **Nested Git Submodules:** Complex, harder to work with initially

**Review Trigger:**
- When team grows beyond 5 developers
- When services have independent release cycles
- When cross-service changes become rare
- When operational complexity justifies separation

---

## Decision 12: AWS Cognito for Authentication

**Date:** 2026-03-09

**Status:** Accepted

**Context:**
- Initial design used custom OAuth implementation with social providers
- Custom session management with DynamoDB storage
- OAuth client code complexity and maintenance burden
- Cost and operational overhead of custom implementation
- Need for secure, scalable authentication

**Decision:**
Switch from custom OAuth implementation to AWS Cognito User Pools for authentication and session management.

**Rationale:**
1. **Reduced Complexity:**
   - Cognito handles OAuth flows with social providers automatically
   - No need to implement OAuth client manager
   - No custom session management code needed
   - Eliminates ~500+ lines of OAuth and session code

2. **Better Security:**
   - Industry-standard JWT tokens
   - Built-in token validation and refresh
   - Managed security updates by AWS
   - Automatic HTTPS enforcement

3. **Cost Efficiency:**
   - Cognito: ~$5-10/month for current target (MAU pricing)
   - Eliminates DynamoDB session storage costs
   - Eliminates validation Lambda invocations
   - Similar total cost to custom implementation

4. **Operational Simplicity:**
   - No OAuth credential management in Secrets Manager
   - API Gateway Cognito Authorizer validates tokens automatically
   - Built-in user management UI
   - Automatic token rotation and refresh

5. **Faster Development:**
   - Eliminates Tasks 6-7 (OAuth client, session manager)
   - Simpler Lambda handlers (no OAuth code)
   - Faster time to market

**Architecture Changes:**

**Before (Custom OAuth):**
```
Frontend → API Gateway → Lambda (OAuth) → Social Providers
                      → Lambda (Session) → DynamoDB (sessions)
```

**After (Cognito):**
```
Frontend → Cognito (OAuth) → Social Providers
        → API Gateway (Cognito Authorizer) → Lambda (business logic)
```

**Session Management:**
- **Before:** Custom session tokens stored in DynamoDB, validated on every request
- **After:** JWT tokens (ID, Access, Refresh) issued by Cognito, validated by API Gateway

**Token Flow:**
1. User authenticates via Cognito Hosted UI or SDK
2. Cognito returns JWT tokens (ID token, Access token, Refresh token)
3. Frontend stores tokens (secure storage, httpOnly cookies)
4. API calls include Access token in Authorization header
5. API Gateway validates JWT automatically (no Lambda code)
6. Lambda receives validated user info in event context

**Consequences:**

*Positive:*
- Eliminates OAuth client manager implementation
- Eliminates custom session manager implementation
- No DynamoDB session storage needed
- Faster token validation (JWT signature vs DB query)
- Built-in token refresh mechanism
- Reduced Lambda code and complexity
- Industry-standard authentication

*Negative:*
- AWS vendor lock-in for authentication
- Harder to revoke tokens immediately (need token blacklist)
- Client-side token storage (XSS risk - mitigated separately)
- Less control over token format and claims
- Cognito Hosted UI customization limitations

*Mitigations:*
- XSS protection: httpOnly cookies, CSP headers, input sanitization (TODO)
- Token revocation: Implement token blacklist in DynamoDB if needed
- Custom UI: Use Cognito SDK instead of Hosted UI for full control
- Vendor lock-in: Keep business logic separate from auth layer

**Cost Comparison:**

*Custom OAuth (Original):*
- Lambda (OAuth + Session): ~$5/month
- DynamoDB (sessions): ~$1/month
- Secrets Manager (OAuth creds): ~$1/month
- Total: ~$7/month

*Cognito:*
- Cognito User Pools: ~$5-10/month (MAU pricing, 50 MAU free tier)
- Lambda (business logic only): ~$3/month
- No session storage needed
- Total: ~$8-13/month

**Net difference: +$1-6/month, but significantly less code and complexity**

**Implementation Changes:**
1. Remove OAuth client manager code
2. Remove session manager code
3. Remove session-related DynamoDB items
4. Add Cognito User Pool to SAM template
5. Add Cognito Authorizer to API Gateway
6. Update Lambda handlers to use Cognito user context
7. Update data models (remove Session, add Cognito user attributes)
8. Update frontend to use Cognito SDK

**Alternatives Considered:**
1. **Keep Custom OAuth:** More control but higher complexity
2. **Auth0/Okta:** Third-party, higher cost, additional vendor
3. **Firebase Auth:** Google-specific, not AWS-native

**Review Trigger:**
- If Cognito costs exceed $20/month
- If token revocation becomes critical requirement
- If need to migrate away from AWS

---

## Future Decisions to Make

### 1. Multi-Factor Authentication (MFA)
- **When:** After initial launch and user feedback
- **Options:** TOTP, SMS, WebAuthn
- **Considerations:** Cost, user experience, security requirements

### 2. Email Verification
- **When:** If account security becomes a concern
- **Options:** Social provider verification (current), separate email verification
- **Considerations:** User friction, security requirements

### 3. Migration to Fargate
- **When:** Traffic consistently >500 RPS or cold starts problematic
- **Trigger:** Cost per request becomes competitive
- **Plan:** Dual-write strategy, gradual traffic shift

### 4. Database Migration
- **When:** Need complex queries or analytics
- **Options:** Add Aurora Serverless for analytics, keep DynamoDB for OLTP
- **Considerations:** Cost, query complexity, data consistency

### 5. Observability Enhancement
- **When:** After initial launch
- **Options:** X-Ray tracing, custom metrics, distributed tracing
- **Considerations:** Cost, debugging needs, performance monitoring

---

## Review Schedule

This document should be reviewed:
- After initial launch (3 months)
- When traffic patterns change significantly
- When new requirements emerge
- Quarterly as part of architecture review

## References

- [COMPARISON.md](./COMPARISON.md) - Detailed Fargate vs Serverless comparison
- [design.md](./design.md) - Technical design document
- [requirements.md](./requirements.md) - Functional requirements
- [archive-fargate-design/](./archive-fargate-design/) - Original Fargate design


---

## Decision 13: Local Test Validation Before Push

**Date:** March 10, 2026

**Status:** Implemented

**Context:**
- Need to maintain code quality and prevent broken tests from being pushed to the repository
- CI/CD pipeline failures waste resources and slow down development
- Early detection of issues improves developer experience and code review efficiency

**Decision:**
All tests must pass locally before pushing changes to the PR branch on remote.

**Rationale:**
1. **Quality Assurance:**
   - Catches issues early before they reach the remote repository
   - Prevents CI/CD pipeline failures and wasted resources
   - Ensures code quality standards are met before peer review

2. **Developer Experience:**
   - Reduces feedback cycles and speeds up the review process
   - Developers get immediate feedback on their changes
   - Prevents embarrassing broken commits

3. **Cost Efficiency:**
   - Reduces unnecessary CI/CD runs
   - Saves compute resources and time
   - Faster iteration cycles

**Implementation:**
- Created a "Run Tests Before PR" hook that can be manually triggered
- Hook runs full test suite with coverage reporting: `pytest --cov=src --cov-report=term-missing -v`
- Developers should run this hook before pushing changes to verify all tests pass
- Hook is located in `.kiro/hooks/pre-pr-test-check.json`

**Usage:**
1. Make code changes
2. Trigger "Run Tests Before PR" hook from Agent Hooks panel or command palette
3. Verify all tests pass and coverage is acceptable
4. Push changes to PR branch on remote

**Consequences:**

*Positive:*
- Higher code quality before peer review
- Faster feedback cycles
- Reduced CI/CD failures
- Better developer experience

*Negative:*
- Requires developer discipline to run hook
- Adds extra step before pushing
- May slow down rapid iteration

*Mitigations:*
- Hook is easy to trigger (one click)
- Can be automated in future with pre-push git hooks
- Documentation in README reminds developers

**Alternatives Considered:**
1. **Mandatory Pre-Push Git Hook:** More enforcement but less flexibility
2. **CI/CD Only:** Slower feedback, wasted resources
3. **No Local Testing:** Poor code quality, frequent CI failures

**Review Trigger:**
- If developers frequently push broken tests
- If CI/CD failure rate exceeds 10%
- If need to enforce with mandatory git hooks
