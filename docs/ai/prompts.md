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
> `JOB_ANALYSIS_PROMPT_VERSION`, `JOB_ANALYSIS_SCHEMA_VERSION` — prompt "1.4.0",
> schema "1.1.0").
> It is executed by the `analyze` node of the JobAnalysisGraph via
> `LLMService.generate_structured(prompt, schema=…, timeout=240)` — exactly
> one LLM call per job.

Also removed: `jobs/infrastructure/ai/prompts/tailor.py`, `cover_letter.py`,
`generate_cover_letter.md`, `tailor_resume.md`, and the legacy resume/cover
letter `.txt` prompt files (`resume/step7_cover_generate.txt`,
`resume/step_resume_generate.txt`) that backed the legacy Socket.IO pipeline —
resume/cover letter generation was removed from the platform.

## Usage

The v2 `job.analyze` prompt is a self-contained builder:

```python
from processing.application.services.job_analysis_prompt import (
    JOB_ANALYSIS_PROMPT_VERSION,   # "1.4.0"
    JOB_ANALYSIS_SCHEMA_VERSION,   # "1.1.0"
    build_job_analysis_prompt,
    build_job_analysis_output_schema,
)

prompt = build_job_analysis_prompt(
    job_text,
    profile_text,
    scoring_rules,
    resume_text,
    profile_documents,  # structured candidate profile OR raw resume + LinkedIn
)
schema = build_job_analysis_output_schema()

# Executed exactly once per job by the analyze node:
resp = llm.generate_structured(prompt=prompt, schema=schema, timeout=240)
```

### Profile documents (since v1.4.0)

The `prepare_profile` node now reads the structured **Candidate Profile** when
one exists and uses it as the primary document section, falling back to the raw
resume / LinkedIn text only when no profile has been built yet.

- **Candidate profile present** → `profile_documents` is the formatted canonical
  profile (header, skills with level/confidence/years/evidence, experience,
  projects, education, certificates, interests, languages) via
  `build_candidate_profile_text` (`job_analysis_inputs.py`), truncated to a
  6000-character budget. `profile_text` is also built from the profile's skills
  (richer evidence metadata) instead of the curated skills registry.
- **No candidate profile** → legacy behavior: raw labeled sections:

  ```
  RESUME TEXT (latest):
  …
  LINKEDIN PROFILE TEXT (latest):
  …
  ```

  via `build_profile_documents_text`. The resume is the authoritative source for
  skills and seniority; LinkedIn is supplementary. Each source is truncated
  independently to a 6000-character budget.

A DB failure reading the profile degrades gracefully to the raw-document path
and records an error, so job analysis never blocks on the profile. Fit scoring
is based primarily on the structured profile when provided (prompt v1.4.0);
otherwise on the resume text as before. Builders live in
`processing/application/services/job_analysis_inputs.py`
(`build_candidate_profile_text`, `build_profile_documents_text`).

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
