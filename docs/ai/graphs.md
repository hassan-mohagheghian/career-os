# Graph Reference

## Job Processing Graph (v2 — two-phase)

A v2 job processing run executes **two LangGraph phases** inside a single
ProcessingExecution.

**Phase 1 — JobContextPreparationGraph** (no LLM)
**Name**: `job_context_preparation`
**Entry**: `load_job`
**Finish**: `context_ready`

```
START → load_job → collect_sources → fetch_sources → extract_content
      → build_context → validate_context → persist_context
      → context_ready | execution_failed → END
```

`persist_context` writes the combined text to the job row
(`raw_description` + `description`) via `JobService.persist_prepared_context`
so the analysis phase has a durable LLM input.

**Phase 2 — JobAnalysisGraph** (exactly one LLM call)
**Name**: `job_analysis`
**Entry**: `load_context`
**Finish**: `analysis_ready`

```
START → load_context → prepare_profile → analyze → extract_skills → score
      → recommend → summarize → persist
      → analysis_ready | execution_failed → END
```

Exactly **one LLM call** per job: `analyze` runs the versioned `job.analyze`
prompt via `LLMService.generate_structured(prompt, schema=…, timeout=240)`.
Scoring/recommendation are deterministic (`job_analysis_scoring.py`):
`overall = round(fit*0.6 + success*0.4)`, `apply` ≥ 80 / `consider` ≥ 60 /
else `skip`. `persist` writes the `jobs` row projection, the `summaries` row,
and the canonical `job_analysis` table (schema `job`).

If Phase 1 ends with `execution_failed`, Phase 2 is skipped. The runner
(`processing/infrastructure/runner/execution_runner.py`) runs Phase 1, then
invokes the analysis graph with the same `JobProcessingState`.

## Job Processing Graph (legacy)

**Name**: `job_processing`
**Entry**: `validate_input`
**Finish**: `completion_event`

```
START → validate_input → fetch_url → fallback_to_notes → extract_raw_content
      → clean_content → extract_structured_data → analyze_job → extract_skills
      → score_job → generate_summary → persist_results → completion_event → END
```

**Typed Output**: `JobAnalysisOutput`
**Retry Nodes**: `extract_raw_content`, `score_job`

## Company Processing (removed graph)

The standalone `company_processing` graph was **removed**. Companies now run
through the shared two-phase ProcessingExecution workflow (`COMPANY_PROCESSING`):
context preparation without an LLM call, then a single-LLM analysis — the same
pattern used by jobs.

## Resume / Cover Letter Generation (application artifacts)

The standalone `resume_generation` and `cover_letter_generation` graphs were
**removed** in an earlier phase. Tailored resumes and cover letters are now
generated per application by the `ApplicationIntelligenceGraph`
(`APPLICATION_PREPARATION` / `APPLICATION_RESUME` / `APPLICATION_COVER_LETTER`
executions), a single-graph workflow that reuses the job analysis, company and
candidate context builders (no re-analysis). See
`docs/ai/application-intelligence.md`.

## Skill Extraction Graph

**Name**: `skill_extraction`
**Entry**: `load_jobs`
**Finish**: `completion_event`

```
START → load_jobs → extract_skills → categorize_skills
      → enrich_skills → completion_event → END
```

**Typed Output**: `SkillExtractionOutput`

## Career Insights Graph

**Name**: `insights_generation`
**Entry**: `overview`
**Finish**: `aggregate`

```
START → overview → skills → market → companies
      → networking → opportunities → aggregate → END
```

**Typed Output**: `CareerInsightsOutput`
**Retry Nodes**: All section nodes (1 retry each)

### Child Graphs (independently executable)

| Graph | Entry | Finish |
|-------|-------|--------|
| `insights_overview` | `collect_data` | `generate_summary` |
| `insights_skills` | `load_skills` | `generate_recommendations` |
| `insights_market` | `analyze_demand` | `generate_report` |
| `insights_companies` | `load_companies` | `generate_shortlist` |
| `insights_networking` | `analyze_connections` | `generate_recommendations` |
| `insights_opportunities` | `load_opportunities` | `generate_action_plan` |

## Generate All Graph

**Name**: `generate_all`
**Entry**: `job_processing`
**Finish**: `completion_event`

```
START → job_processing → resume_generation
      → cover_letter_generation → skill_extraction
      → insights_generation → completion_event → END
```

**Typed Output**: Aggregated dict with all stage results
**Retry Nodes**: All stage nodes (1 retry each)

## Adding a New Graph

1. Create `apps/backend/ai/infrastructure/graphs/{name}/graph.py`
2. Implement `build_{name}_graph() -> GraphBuilder`
3. Add typed output model to `runtime/state.py`
4. Register in `graphs/__init__.py`
5. Add prompts to `prompts/{name}/`
6. Write tests in `tests/ai/infrastructure/graphs/`
