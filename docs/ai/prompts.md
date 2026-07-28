# Prompt Management Platform

## Principles

1. **No prompt strings embedded in workflows** — All prompts are defined as templates using `ChatPromptTemplate` from `langchain_core.prompts`.
2. **No manual concatenation** — Templates are rendered by the `PromptTemplate` class, never concatenated manually.
3. **Ownership follows bounded contexts** — Each bounded context owns its prompts. Prompts are registered under identifiers like `job.extract`, `company.analyze`, `resume.tailor`.
4. **Versioned** — Every prompt has an explicit version. Prompts are never silently replaced.
5. **Typed inputs** — Every prompt accepts a strongly typed Pydantic input model.
6. **Structured outputs** — Prompts instruct the LLM to return structured JSON or Pydantic models.
7. **Provider-independent** — Templates contain no provider-specific syntax. Providers adapt prompts when necessary.

## Organization

```
ai/infrastructure/prompts/
├── __init__.py              # Public API exports
├── base.py                  # PromptType enum, PromptSpec, PromptVersion
├── template.py              # PromptTemplate wrapper around ChatPromptTemplate
├── inputs.py                # Typed Pydantic input models
├── components.py            # Reusable prompt components
├── registry.py              # PromptRegistry with versioning
├── observability.py         # PromptLogger
├── register_all.py          # Bootstrapper to register all prompts
├── jobs/
│   ├── __init__.py
│   ├── extract.py           # job.extract — Job extraction prompt
│   ├── score.py             # job.score — Job scoring prompt
│   └── summarize.py         # job.summary — Job summary prompt
├── companies/
│   ├── __init__.py
│   ├── extract.py           # company.extract — Company data extraction
│   └── analyze.py           # company.analyze — Company intelligence
├── resume/
│   ├── __init__.py
│   ├── tailor.py            # resume.tailor — Resume tailoring
│   └── cover_letter.py      # resume.cover-letter — Cover letter generation
├── skills/
│   ├── __init__.py
│   ├── extract.py           # skills.extract — Skill extraction
│   └── roadmap.py           # skills.roadmap — Learning roadmap
└── insights/
    ├── __init__.py
    └── overview.py           # insights.overview — Career insights
```

## Usage

### Rendering a prompt

```python
from ai.infrastructure.prompts import get_prompt

# Simple string rendering
result = get_prompt("job.extract", content="Senior Python Developer at Google...")

# With typed input model
from ai.infrastructure.prompts.inputs import JobExtractionInput
inp = JobExtractionInput(content="Senior Python Developer at Google...")
result = get_prompt("job.extract", **inp.model_dump())
```

### Using the registry

```python
from ai.infrastructure.prompts import get_registry

registry = get_registry()
prompt = registry.get("job.score")
spec = prompt.spec
print(f"Version: {spec.version}, Owner: {spec.owner}")

# Get specific version
prompt_v1 = registry.get("job.extract", version="1.0.0")

# List prompts
for spec in registry.all_specs():
    print(f"{spec.identifier} v{spec.version} [{spec.owner}]")
```

### Versioning

```python
registry.create_version(
    identifier="job.extract",
    template="New template {content}",
    version="2.0.0",
    description="Major revision with improved extraction format",
)
```

### Reusable components

```python
from ai.infrastructure.prompts.components import (
    tone_instructions,
    JSON_RULES,
    FORMATTING_RULES,
)

# Combine components
from ai.infrastructure.prompts import build_components
components = build_components(tone_instructions("technical"), JSON_RULES)
```
