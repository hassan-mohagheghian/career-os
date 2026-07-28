# Prompt Registry

The `PromptRegistry` is the centralized access point for all prompts.

## Architecture

```
PromptRegistry
├── register(prompt)         — Register a PromptTemplate
├── get(identifier, version) — Get a PromptTemplate by identifier + version
├── render(identifier, ...)  — Shortcut: get + render
├── create_prompt(...)       — Create and register a prompt from a string
├── create_version(...)      — Create a new version of an existing prompt
├── list_identifiers()       — List all registered identifiers
├── list_versions(id)        — List all versions of a prompt
├── list_by_owner(owner)     — List prompts by bounded context
├── list_by_tags(tags)       — List prompts by tags
├── exists(identifier)       — Check if a prompt exists
└── deregister(...)          — Remove a prompt
```

## Module-level convenience functions

```python
from ai.infrastructure.prompts import get_prompt, register_prompt, get_registry

# Quick render
result = get_prompt("job.extract", content="...")

# Quick registration
register_prompt("my.custom", "Template {var}", owner="my-context")

# Access the registry
registry = get_registry()
```

## Registered prompts

| Identifier | Version | Owner | Type | Tags |
|---|---|---|---|---|
| `job.extract` | 1.0.0 | jobs | extraction | job, extraction |
| `job.score` | 1.0.0 | jobs | evaluation | job, scoring |
| `job.summary` | 1.0.0 | jobs | summarization | job, summary |
| `company.extract` | 1.0.0 | companies | extraction | company, extraction |
| `company.analyze` | 1.0.0 | companies | evaluation | company, analysis |
| `resume.tailor` | 1.0.0 | resume | user | resume, tailoring |
| `resume.cover-letter` | 1.0.0 | resume | user | resume, cover-letter |
| `skills.extract` | 1.0.0 | skills | extraction | skills, extraction |
| `skills.roadmap` | 1.0.0 | skills | summarization | skills, roadmap |
| `insights.overview` | 1.0.0 | career | summarization | career, insights |
