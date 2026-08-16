# Processing Content Reuse & Candidate Inputs

## Purpose

Documents two behaviours of the job and company processing pipelines:

1. **LLM-error content reuse** — reusing already-fetched/extracted content on a
   reprocess that follows an **analysis (LLM) failure**, so the run does not
   re-fetch and re-extract the same sources.
2. **Candidate inputs in company analysis** — feeding the candidate's resume /
   LinkedIn / candidate profile into the **company** analysis prompt (jobs already
   did this).

---

## 1. Content reuse on LLM-error reprocess

### Rule

A job/company run **reuses** the previously persisted prepared content (the
aggregated `combined_text` stored in `jobs.raw_description` / `description` and
`companies.raw_content`) — skipping the Fetch + Extract steps — **only** when:

- the target already has non-empty persisted prepared content, **and**
- the **most recent** prior execution for that target is `FAILED` (i.e. it failed
  at the LLM/analysis step, after context had already been prepared).

Everything else runs **from scratch** (fetch + extract + build context):

- a **first process** (no prior execution / no content), and
- a **reprocess of a completed** target.

### Why

Context preparation (fetch + extract) is cheap but non-deterministic and
network-bound; the analysis step is where failures usually happen. When a run
already prepared content and only the LLM step failed, re-fetching the same URLs
is wasteful and can fail again for unrelated reasons.

### Mechanism

`ProcessingExecutionRunner._reuse_available(execution, session)` decides:

```python
reuse = target has persisted content
        and latest prior execution for target is FAILED
```

In `_run_workflow`, when reuse is true the runner **skips the context preparation
graph** and invokes the **analysis graph directly** on a fresh state — the
analysis `LoadContextNode` rebuilds the processing context from the persisted
content. Otherwise it runs prep-then-analysis as before.

This requires no DB schema change: reuse is inferred from existing persisted
content + execution history (`SQLAlchemyProcessingExecutionRepository.list_by_target`).

---

## 2. Candidate inputs in company analysis

The candidate's latest **resume**, **LinkedIn** profile and **candidate profile**
are loaded in the analysis phase and fed to the company LLM as labeled extra
context, mirroring the job analysis prompt.

- `PrepareCompanyNode` loads the candidate profile and latest resume/LinkedIn raw
  text (via `source_repo` + `candidate_profile_repo`) and sets
  `analysis_context["resume_text"]` and `analysis_context["profile_documents"]`
  (reusing the shared `build_resume_text` / `build_profile_documents_text` /
  `build_candidate_profile_text` builders).
- `build_company_analysis_prompt` accepts `resume_text` and `profile_documents`
  and the `company_combined_analyze.txt` template renders them under labeled
  `CANDIDATE RESUME` / `CANDIDATE PROFILE / LINKEDIN` sections.
- `AnalyzeCompanyNode` passes them into the prompt.

When no candidate input exists, the sections render with the standard placeholders
(`(no resume available)`, etc.).

---

# Related Documents

- `docs/domain/processing/processing-execution.md`
- `docs/api/processing/retry-processing.md`
- `docs/workflows/job-processing.md`
- `docs/ai/job-processing-context.md`