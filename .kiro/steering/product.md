---
inclusion: always
---

# Product Context

Yomite is an application that provides an immersive, rich reading experience for users.

## Architecture

The application follows a modular architecture with separate sub-projects that may eventually become independent services or repositories:

- **Sub-Project 1: User Management** - Handles user registration, authentication, profiles, and preferences
- **Sub-Project 2: TBD** - Future reading experience features

## Current State

- Git version control initialized
- Kiro AI assistant configured
- Initial scope: User Registration Service

## Development Methodology

Use spec-driven development for all features:

1. Create requirements or design document first
2. Define correctness properties for property-based testing
3. Implement with tests validating those properties
4. Document architectural decisions

## AI Assistant Guidelines

When working in this codebase:

- Always propose creating a spec before implementing features
- Ask clarifying questions about requirements before starting work
- Suggest property-based tests for validating correctness
- Keep implementations minimal and focused on requirements
- Document design decisions and trade-offs made
