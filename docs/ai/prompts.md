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
> `JOB_ANALYSIS_PROMPT_VERSION`, `JOB_ANALYSIS_SCHEMA_VERSION` — prompt "1.1.0",
> schema "1.0.0").
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
    JOB_ANALYSIS_PROMPT_VERSION,   # "1.1.0"
    JOB_ANALYSIS_SCHEMA_VERSION,   # "1.0.0"
    build_job_analysis_prompt,
    build_job_analysis_output_schema,
)

prompt = build_job_analysis_prompt(
    job_text,
    profile_text,
    scoring_rules,
    resume_text,
    profile_documents,  # latest resume + LinkedIn, labeled sections
)
schema = build_job_analysis_output_schema()

# Executed exactly once per job by the analyze node:
resp = llm.generate_structured(prompt=prompt, schema=schema, timeout=240)
```

### Profile documents (since v1.1.0)

The `prepare_profile` node fetches the latest resume (`original_*`) and the
latest LinkedIn profile (`linkedin_*`) separately and passes them into the
prompt as labeled sections:

```
RESUME TEXT (latest):
…
LINKEDIN PROFILE TEXT (latest):
…
```

The resume is the **authoritative** source for skills and seniority; LinkedIn
is supplementary (current title, company, tenure, achievements). Each source is
truncated independently to a 6000-character budget so neither can crowd out the
other. If neither document exists the builder falls back to the resume-only
section. Builders live in
`processing/application/services/job_analysis_inputs.py`
(`build_profile_documents_text`).

The prompt and its output JSON schema are versioned together and live in
`processing/application/services/job_analysis_prompt.py`.

### Company combined analysis (since v1.1.0)

The company analysis is a **single combined LLM call per company** executed by
the `analyze_company` node of the CompanyAnalysisGraph. It is built by
`processing/application/services/company_analysis_prompt.py`
(`build_company_analysis_prompt`, `build_company_analysis_output_schema`,
`COMPANY_ANALYSIS_PROMPT_VERSION` = `COMPANY_ANALYSIS_SCHEMA_VERSION` =
"1.1.0") from the template
`companies/infrastructure/ai/prompts/company/company_combined_analyze.txt`.

The combined output must stay **short enough to never be truncated** by the
provider's output-token ceiling (`deepseek-v4-flash-free` caps around ~2.7K
output tokens). The template therefore enforces a tight size budget:

- `extraction.description`: at most 50 words.
- Every explanation field: at most 15 words.
- factor/risk/positive-signal lists: at most 3 items each.
- Total JSON under ~1600 words.
- Intelligence sections must add **new** insight, not duplicate the
  extraction facts.

The `intelligence` sections (overview, culture_analysis, benefits_analysis,
…) intentionally enumerate only the sub-fields the frontend renders; the
remaining sub-fields were dropped so a complete, valid JSON reliably fits the
output window. The output is validated against `CompanyCombinedAnalysisOutput`
(`processing/application/services/company_analysis_validation.py`) before it
is persisted.
