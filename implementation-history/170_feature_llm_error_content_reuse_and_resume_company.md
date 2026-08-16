# Prompt 170 - LLM-Error Content Reuse + Resume in Company Processing

## Objective

Two related processing improvements, applied to **both job and company**:

1. **LLM-error content reuse**: when a job/company process **failed at the LLM
   (analysis) step**, a reprocess should **skip re-fetch + re-extract** and reuse
   the already-persisted prepared content. A **first process** or a **reprocess
   of a completed** target must run **from scratch** (fetch + extract).
2. **Resume in company processing**: feed the candidate resume/LinkedIn (and
   candidate profile) into the **company** analysis LLM prompt, exactly like jobs
   already do via `PrepareProfileNode`.

## Current State

- Both pipelines run **context prep** (Fetch → Extract → BuildContext →
  PersistContext, no LLM) then **analysis** (one LLM call). `execution_runner.py`
  always runs the prep graph then the analysis graph (`:156-167` job, `:190-201`
  company). Fetch/extract always re-run on reprocess (`fetch_sources_node.py:51`).
- Persisted prepared content: `jobs.raw_description`/`description` =
  `JobService.persist_prepared_context`; `companies.raw_content` =
  `CompanyService.persist_prepared_context`. The analysis `LoadContextNode`
  already rebuilds context from these (`load_context_node.py:43` job, `:44` company).
- The runner marks a failed run as `ExecutionStatus.FAILED` with
  `error_message` (`execution_runner.py:82-84`). Target rows are **not** set to
  `failed`; the failure signal lives on the `ProcessingExecution`.
- `ExecutionActionService.reprocess` creates a brand-new execution
  (`execution_actions.py:132-153`). There is no resume-from-failure mechanism.
- Resume/candidate source is wired **only** into job analysis:
  `PrepareProfileNode` (`prepare_profile_node.py`) loads resume/LinkedIn via
  `source_repo` + `candidate_profile_repo` and sets `analysis_context`
  `resume_text` / `profile_documents` / `profile_text`; `AnalyzeNode` passes them
  to `build_job_analysis_prompt`. Reusable builders: `build_resume_text`,
  `build_profile_documents_text`, `build_candidate_profile_text`
  (`job_analysis_inputs.py:25,35,52`).
- The **company** pipeline has no candidate input: `PrepareCompanyNode`
  (`prepare_company_node.py`) only loads `rule_repo`; `AnalyzeCompanyNode`
  (`analyze_company_node.py:103`) calls `build_company_analysis_prompt(company_text,
  company_type, scoring_rules)` (`company_analysis_prompt.py:114`); the prompt
  template is `companies/infrastructure/ai/prompts/company/company_combined_analyze.txt`.
  `assembly.build_company_analysis_graph` (`assembly.py:127`) wires only
  `rule_repo` + `llm_service`.
- `SQLAlchemyProcessingExecutionRepository.list_by_target(target_type, target_id)`
  returns executions for a target; `self._repository` may be `None` on the runner
  (built from session in `run()`).

## Changes

### 1. LLM-error content reuse — `execution_runner.py`

Add a private helper `_should_reuse_content(execution, session) -> bool` that
returns true only when **all** hold:
- target is `job` or `company`; and
- the target has non-empty persisted prepared content
  (`jobs.raw_description`/`description`; `companies.raw_content`); and
- among executions for the target (excluding the current one), the **latest** is
  `ExecutionStatus.FAILED`.

Use it in the JOB and COMPANY branches of `_run_workflow`: when true, skip the
context preparation graph and invoke the **analysis graph directly** on a fresh
state (the analysis `LoadContextNode` already rebuilds context from the
persisted content). Otherwise keep the current prep-then-analysis flow. This
makes first process / completed-reprocess run from scratch and failed-at-analysis
reprocess reuse cached content — no schema change.

### 2. Resume in company processing

- `PrepareCompanyNode`: accept `source_repo` + `candidate_profile_repo`; load the
  candidate profile, latest resume/LinkedIn raw text, and set
  `analysis_context["resume_text"]` / `["profile_documents"]` (reuse the
  `job_analysis_inputs` builders), like `PrepareProfileNode`.
- `build_company_analysis_prompt`: add `resume_text: str = ""` and
  `profile_documents: str = ""` params and pass them into the template loader.
- company template `company_combined_analyze.txt`: add labeled resume/profile
  placeholder sections.
- `AnalyzeCompanyNode`: read `resume_text` / `profile_documents` from context and
  pass to the prompt builder.
- `CompanyAnalysisGraph.__init__`: accept `source_repo` + `candidate_profile_repo`
  and pass to `PrepareCompanyNode`.
- `assembly.build_company_analysis_graph`: wire
  `SQLAlibabaCandidateSourceRepository` + `SQLAlibabaCandidateProfileRepository`.

### Docs

- `docs/processing/` — document the reuse rule (reuse only after analysis/LLM
  failure; first process and completed reprocess run from scratch) and the
  resume-in-company analysis input.
- `docs/api/API.md` if needed.

## Testing

- Backend TDD:
  - `_should_reuse_content`: false for first process (no content / no failed
    prior), false when latest prior execution is COMPLETED, true when latest prior
    is FAILED + content present, false for non-job/company targets.
  - Runner integration: a failed-at-analysis reprocess skips fetch/extract (fetch
    not called) and produces analysis from persisted content; a completed reprocess
    and a first process still call fetch.
  - `PrepareCompanyNode` populates `resume_text`/`profile_documents`; company prompt
    includes resume when provided.
- Frontend: none expected (no UI change).

## Constraints

- No DB schema change (reuse is decided from existing content + execution
  history). Do not refactor the legacy worker paths.
- Cross-context: reuse the `job_analysis_inputs` builders (same processing
  context); do not cross bounded-context imports outside `processing`.