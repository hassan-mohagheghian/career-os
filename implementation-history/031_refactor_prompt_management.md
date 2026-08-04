# Sprint 10 — Build a Prompt Management Platform

## ROLE

You are a Principal AI Architect, Prompt Engineering Expert, LangChain Expert, LangGraph Expert, and Software Architect.

Your task is to redesign the entire prompt architecture for the project.

The project already uses:

- FastAPI
- LangChain
- LangGraph
- PostgreSQL
- SQLAlchemy
- Redis
- ARQ
- DDD
- Hexagonal Architecture

Prompt engineering is now considered a first-class architectural concern.

Prompts must become modular, versioned, testable, reusable, provider-independent, and maintainable.

Business behavior must remain unchanged.

---

# OBJECTIVES

Build a centralized Prompt Platform.

No workflow should embed prompt strings.

No prompt should be manually concatenated.

Every prompt should be rendered from reusable templates.

---

# PROMPT ORGANIZATION

Every bounded context owns its prompts.

Example:

jobs/
    prompts/

companies/
    prompts/

resume/
    prompts/

career/
    prompts/

skills/
    prompts/

sites/
    prompts/

shared/
    prompts/

Avoid one global prompt folder.

Ownership follows the bounded context.

---

# PROMPT TYPES

Support:

System Prompt

Developer Prompt

User Prompt

Tool Prompt

Extraction Prompt

Validation Prompt

Repair Prompt

Summarization Prompt

Classification Prompt

Evaluation Prompt

Reflection Prompt

---

# TEMPLATE ENGINE

Use LangChain ChatPromptTemplate.

Avoid manual string formatting.

Support:

MessagesPlaceholder

Partial Variables

Dynamic Variables

Conditional Sections

Reusable Components

Composable Templates

---

# PROMPT REGISTRY

Implement a Prompt Registry.

Workflows request prompts by identifier.

Example:

job.extract

job.analyze

job.summary

company.extract

resume.score

roadmap.generate

The registry resolves the current implementation.

---

# PROMPT VERSIONING

Every prompt has:

Identifier

Version

Description

Owner

Supported Providers

Input Schema

Output Schema

Tags

Changelog

Prompt version must be explicit.

Never silently replace prompts.

---

# INPUT VALIDATION

Every prompt accepts a strongly typed input model.

Use Pydantic.

Avoid dictionaries.

Example:

JobExtractionInput

CompanyAnalysisInput

ResumeSummaryInput

---

# OUTPUT VALIDATION

Every prompt should return structured output.

Prefer structured JSON or Pydantic models.

Avoid parsing arbitrary text.

---

# PROVIDER INDEPENDENCE

Prompt templates must never contain provider-specific syntax.

Providers adapt prompts when necessary.

The workflow remains provider-agnostic.

---

# REUSABLE COMPONENTS

Create reusable prompt fragments.

Examples:

Tone Instructions

Formatting Rules

Output Constraints

JSON Rules

Safety Instructions

Reasoning Instructions

Language Selection

Reuse them through composition.

---

# TESTING

Every prompt should have tests.

Validate:

Rendering

Variables

Missing Inputs

Structured Output

Regression

Golden Output

---

# OBSERVABILITY

Log:

Prompt Identifier

Prompt Version

Provider

Execution Time

Token Count

Rendered Size

Failures

---

# DOCUMENTATION

Create:

docs/ai/prompts.md

docs/ai/prompt-registry.md

docs/ai/prompt-versioning.md

docs/ai/prompt-testing.md

docs/adr/010-prompt-platform.md

---

# FUTURE READINESS

The architecture should allow future migration to:

- LangSmith Prompt Hub
- OpenAI Prompt Management
- LangFuse
- PromptLayer
- Any external prompt registry

without modifying workflows.

---

# ACCEPTANCE CRITERIA

✔ No prompt strings embedded in workflows.

✔ All prompts use LangChain ChatPromptTemplate.

✔ Prompts are versioned.

✔ Prompts have typed input models.

✔ Prompt rendering is centralized.

✔ Prompt ownership follows bounded contexts.

✔ Prompt tests exist.

✔ Provider-specific logic is isolated.

✔ Existing AI behavior remains unchanged.
