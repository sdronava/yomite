---
inclusion: always
---

# Project Structure

## Current Organization

```
.
├── .git/              # Git version control
├── .kiro/             # Kiro AI assistant configuration
│   ├── specs/         # Feature specifications
│   └── steering/      # AI guidance documents
└── .vscode/           # VSCode editor settings
```

## Recommended Structure

Organize the project with modularity in mind for potential service separation:

### Modular Architecture
```
.
├── services/
│   ├── user-management/    # Sub-Project 1
│   │   ├── src/           # Backend Python code
│   │   ├── tests/         # Backend tests
│   │   └── infrastructure/ # IaC for this service
│   └── [future-services]/
├── frontend/              # Frontend application
│   ├── src/
│   └── tests/
├── infrastructure/        # Shared infrastructure
├── docs/                  # Documentation
└── docker/               # Container configurations
```

### Source Code
- Organize by sub-project/service for future modularity
- Separate application code from tests
- Group related functionality into modules or packages

### Tests
- Keep tests close to the code they test or in a parallel `tests/` directory
- Use descriptive test file names (e.g., `*.test.*`, `*.spec.*`, or `*_test.*`)
- Include property-based tests for critical correctness properties

### Documentation
- Maintain a README.md at the root with project overview and setup instructions
- Use `.kiro/specs/` for feature specifications and design documents
- Keep API documentation close to the code it documents

### Configuration
- Store configuration files at the root level
- Use environment-specific configs when needed
- Document all configuration options

## File Naming Conventions

- Use consistent casing (kebab-case, snake_case, or camelCase based on language conventions)
- Make names descriptive and searchable
- Avoid abbreviations unless widely understood

## Module Organization

- Keep related functionality together
- Minimize circular dependencies
- Use clear, hierarchical module structure
- Export public APIs explicitly
