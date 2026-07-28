You are a senior software architect and technical documentation engineer.

Your task is to analyze the existing project repository and generate a complete, modern, AI-friendly documentation structure.

Create and populate the following documentation structure:

docs/
│
├── README.md
├── CONTEXT.md
├── ARCHITECTURE.md
├── DOMAIN.md
├── FEATURES.md
├── API.md
├── DEVELOPMENT.md
├── AI_AGENTS.md
├── DECISIONS/
├── RUNBOOKS/
└── CHANGELOG.md


## Goal

The documentation must allow:

1. A new developer to understand the entire project quickly.
2. A senior engineer to understand architectural decisions and trade-offs.
3. An AI coding agent (Cursor, Claude Code, OpenAI Codex, etc.) to understand the project context and safely modify the codebase.

The documentation should be based on the actual repository, not assumptions.

---

# Analysis Phase

Before writing documentation:

1. Analyze the entire repository:
   - Folder structure
   - Source code organization
   - Main modules/packages
   - Dependencies
   - Configuration files
   - Database models
   - APIs
   - Frontend structure (if exists)
   - Infrastructure setup
   - Tests
   - CI/CD
   - Deployment configuration

2. Identify:
   - Main technologies
   - Architectural patterns
   - Design patterns
   - Domain concepts
   - Important workflows
   - External integrations
   - Data flows
   - Security considerations
   - Development conventions

3. Do not invent information.
   - If something is unclear, mark it as "Unknown" or "Needs clarification".
   - Prefer facts from the codebase.

---

# Documentation Requirements

## README.md

Create the main entry point.

Include:

- Project name
- One sentence description
- Main purpose
- Technology stack
- High-level architecture diagram (Mermaid if useful)
- Quick start guide
- Documentation navigation
- Development workflow


---

## CONTEXT.md

Create the project memory/context file for humans and AI agents.

Include:

- What problem this project solves
- Business goal
- Target users
- Core concepts
- Important terminology
- System boundaries
- Main technical constraints
- Key rules that must not be violated

This file should answer:

"If an AI agent reads only one file before modifying the project, what should it know?"


---

## ARCHITECTURE.md

Document the complete system architecture.

Include:

- Architecture style
- Major components
- Component responsibilities
- Communication between components
- Data flow
- Deployment architecture
- Technology choices
- Scalability considerations
- Performance considerations

Use diagrams where useful:

- C4 style diagrams
- Sequence diagrams
- Data flow diagrams

Use Mermaid syntax.


---

## DOMAIN.md

Document domain knowledge.

Include:

- Domain overview
- Core entities
- Value objects
- Relationships
- Business rules
- Domain workflows
- Important invariants

If using DDD:

Document:

- Bounded contexts
- Aggregates
- Domain events
- Domain services


---

## FEATURES.md

Document product capabilities.

For each feature include:

- Feature name
- Purpose
- User story
- Business rules
- Main components involved
- API/UI impact
- Current status

Format:

Feature:
Goal:
Implementation:
Status:


---

## API.md

Document all APIs.

Include:

- API style
- Authentication
- Authorization
- Endpoints
- Request/response examples
- Error handling
- Validation rules
- Versioning strategy

Generate from actual implementation when possible.


---

## DEVELOPMENT.md

Create the developer guide.

Include:

- Local setup
- Requirements
- Environment variables
- Installation steps
- Running the project
- Testing
- Code style
- Naming conventions
- Git workflow
- Debugging guide


---

## AI_AGENTS.md

Create instructions specifically for AI coding agents.

Include:

### Project Understanding

- How the project is structured
- Important directories
- Important files

### Coding Rules

- Existing patterns to follow
- Patterns to avoid
- Naming conventions
- Architecture constraints

### Change Guidelines

Before modifying code:

1. Understand related modules
2. Check existing patterns
3. Avoid unnecessary refactoring
4. Preserve architecture boundaries
5. Add/update tests

### Agent Workflow

Recommended workflow:

1. Analyze
2. Plan
3. Implement
4. Test
5. Document changes


---

## DECISIONS/

Create Architecture Decision Records.

Create files for important existing decisions:

Example:

DECISIONS/
├── ADR-001-architecture-style.md
├── ADR-002-database-choice.md
├── ADR-003-authentication.md

Each ADR:

# Decision

## Context

Why this decision was needed.

## Decision

What was chosen.

## Alternatives

Other options considered.

## Consequences

Positive and negative impacts.


---

## RUNBOOKS/

Create operational guides.

Include when relevant:

- Deployment
- Rollback
- Database migration
- Troubleshooting
- Common production issues
- Monitoring


---

## CHANGELOG.md

Create a structured history.

Include:

- Existing important changes
- Current version
- Future changes format


---

# Documentation Quality Rules

Follow these rules:

- Write concise but complete documentation.
- Use Markdown.
- Use Mermaid diagrams where useful.
- Keep documents maintainable.
- Avoid duplication.
- Prefer explaining "why" over only "what".
- Keep AI readability in mind.
- Use consistent terminology across all files.

---

# Final Output

Generate all documentation files under:

docs/

If a file already exists:
- Improve it.
- Preserve useful information.
- Remove outdated content.

At the end provide:

1. Documentation coverage summary.
2. Missing information that requires human input.
3. Recommended next documentation improvements.
