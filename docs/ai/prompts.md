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

> **Status:** the `ai/infrastructure/prompts/` package (base, template,
> registry, jobs/, companies/, resume/, skills/, insights/) was **removed**.
> The `job.analyze` prompt is now self-contained and versioned in
> `processing/application/services/job_analysis_prompt.py`
> (`build_job_analysis_prompt`, `build_job_analysis_output_schema`,
> `JOB_ANALYSIS_PROMPT_VERSION`, `JOB_ANALYSIS_SCHEMA_VERSION`, both "1.0.0").
> It is executed by the `analyze` node of the JobAnalysisGraph via
> `LLMService.generate_structured(prompt, schema=…, timeout=240)` — exactly
> one LLM call per job.

Also removed: `jobs/infrastructure/ai/prompts/tailor.py`, `cover_letter.py`,
`generate_cover_letter.md`, `tailor_resume.md`. The legacy `.txt` prompt files
(`job_processing/step2/3/4/8.txt`, `resume/step7_cover_generate.txt`,
`resume/step_resume_generate.txt`) are **kept** for the legacy Socket.IO
pipeline.

## Usage

The remaining legacy prompts are plain `.txt` templates consumed directly by
the legacy Socket.IO workers (no runtime registry). The v2 `job.analyze` prompt
is a self-contained builder:

```python
from processing.application.services.job_analysis_prompt import (
    JOB_ANALYSIS_PROMPT_VERSION,   # "1.0.0"
    JOB_ANALYSIS_SCHEMA_VERSION,   # "1.0.0"
    build_job_analysis_prompt,
    build_job_analysis_output_schema,
)

prompt = build_job_analysis_prompt(job_text, profile_text, scoring_rules, resume_text)
schema = build_job_analysis_output_schema()

# Executed exactly once per job by the analyze node:
resp = llm.generate_structured(prompt=prompt, schema=schema, timeout=240)
```

The prompt and its output JSON schema are versioned together and live in
`processing/application/services/job_analysis_prompt.py`.
