# Prompt 062 - Resume & LinkedIn As Job Scoring Context + Fix Upload/View

## Objective

Two coupled goals:

1. **Scoring context**: New job analysis must use **both** the latest uploaded
   resume **and** the latest LinkedIn profile as extra context (combined,
   labeled prompt sections). Resume is primary; LinkedIn is supplementary.
2. **Upload/view correctness**: Fix the broken resume and LinkedIn upload /
   list / delete flows so pasted text saves as a versioned row, appears in the
   Resume page, and the "latest" version of each is what scoring reads.

---

# Read Documentation First

- AGENTS.md (DDD/hexagonal, no raw SQL, structlog, per-context routers)
- API.md, DOMAIN.md (Resume entity)
- docs/ai/prompts.md (job.analyze prompt, versioning)
- docs/workflows/job-processing.md (Phase 2 `prepare_profile`)
- docs/ux/README.md (UX index, design-system layering)
- apps/backend/tests/processing/application/test_job_analysis.py
- apps/backend/jobs/infrastructure/repositories/sa_resume_repository.py
- apps/backend/jobs/domain/repositories/resume_repository.py
- apps/backend/jobs/presentation/api/resumes_router.py
- apps/backend/shared/presentation/api/root_router.py (`linkedin_compat`)
- apps/backend/shared/infrastructure/config/db.py (`_text_to_html`)
- apps/backend/shared/infrastructure/utils.py (`mask_pii`)
- apps/frontend/src/features/resume/components/ResumeTab.tsx

---

# Current State

- Scoring: `prepare_profile_node.py:40` loads `resume OR linkedin` (fallback,
  never combined). Prompt has a single `RESUME TEXT (latest)` section
  (truncated to 6000 chars).
- Uploads are broken:
  - `POST /api/resumes` reads `data["content"]` (frontend sends `raw_text`),
    creates `resume_<hex>` id (frontend filters `original_*`), returns no
    `status`/`version` — the UI's `if (data.status === 'saved')` never fires.
  - `POST`/`DELETE /api/linkedin` do not exist (only a `GET` compat route).
  - Frontend delete sends the `version` as the path segment; APIs expect an `id`.
- Latest semantics: resume ordered by `version DESC`; LinkedIn by `created_at`.

---

# Implementation Steps

## 1. Repository (`sa_resume_repository.py` + `IResumeRepository`)

- `get_latest_linkedin_raw_text` → order by `version DESC` (consistent with
  resume).
- `list_linkedin()` → rows `id LIKE 'linkedin_%'` ordered by `version DESC`.
- `get_next_version(prefix: str) -> int` → `MAX(version)` for rows
  `id LIKE 'prefix%'` + 1 (default 1). ORM only.

## 2. Resume upload service

New `jobs/application/services/resume_service.py`:

- `upload_resume(raw_text, title=None)` → `original_{version}`
- `upload_linkedin(raw_text)` → `linkedin_{version}`

Both: strip → `mask_pii` (from `shared.infrastructure.utils`) → next version →
upsert `{id, title, version, raw_text(masked), content(_text_to_html(raw_text))}`.
Return `{"status": "saved", "version": version, "id": id}`.

Move `_text_to_html` from `shared/infrastructure/config/db.py` into
`shared/infrastructure/utils.py` (db.py re-imports it).

## 3. API routers

- `resumes_router.py` `POST /api/resumes` → body `{raw_text, title?}` → service
  → `{status, version}`. `DELETE /api/resumes/{id}` unchanged.
- New `jobs/presentation/api/linkedin_router.py` mounted at `/linkedin`:
  - `GET /api/linkedin` → `list_linkedin()`
  - `POST /api/linkedin` → `{raw_text}` → service → `{status, version}`
  - `DELETE /api/linkedin/{id}` → `{status: 'deleted', id}`
- Remove `linkedin_compat` from `root_router.py`; include the new router.

## 4. Scoring context (resume + LinkedIn)

- `job_analysis_inputs.py`: add `build_profile_documents_text(resume_raw,
  linkedin_raw)` → labeled sections `RESUME TEXT (latest)` and
  `LINKEDIN PROFILE TEXT (latest)`, each truncated to 6000 chars; when both are
  absent → `"(no resume or LinkedIn profile available)"`.
- `prepare_profile_node.py`: fetch both; set
  `analysis_context["profile_documents"]`.
- `job_analysis_prompt.py`: signature → `build_job_analysis_prompt(job_text,
  user_profile_text, scoring_rules, profile_documents)`. Add a
  `PROFILE DOCUMENTS (resume + LinkedIn):` section and instructions: resume is
  the authoritative source for skills/seniority; LinkedIn adds recent-role,
  project and endorsement context; on conflict, prefer the resume. Bump
  `JOB_ANALYSIS_PROMPT_VERSION` to `1.1.0` (schema unchanged).
- `analyze_node.py`: read `profile_documents` and pass through.

## 5. Frontend

- `ResumeTab.tsx`: delete handlers call `DELETE /api/resumes/{item.id}` and
  `DELETE /api/linkedin/{item.id}` (use `item.id`, not `item.version`).
  Upload handlers already POST `{raw_text}`; backend now returns
  `{status:'saved', version}`.

---

# Testing Requirements

Backend (`uv run pytest apps/backend/tests/ -v`):

- `test_job_analysis.py`:
  - `TestJobAnalysisInputs` → `build_profile_documents_text` (both, resume
    only, linkedin only, neither, per-source truncation).
  - `TestPrepareProfileNode` → both sources combined; drop the linkedin-only
    fallback test.
  - `TestJobAnalysisPrompt` → new section names + prompt version `1.1.0`.
- New `tests/jobs/presentation/api/test_resumes_api.py`:
  - `POST /api/resumes` with `raw_text` → creates `original_{n}`, returns
    `{status:'saved', version}`; second upload bumps the version; row stores
    masked `raw_text` and HTML `content`.
  - `POST /api/linkedin` → creates `linkedin_{n}`.
  - `DELETE /api/resumes/{id}` and `DELETE /api/linkedin/{id}` by id.
  - `GET /api/linkedin` returns only `linkedin_*` rows.
- Update `tests/shared/presentation/api/test_root_router_compat.py`
  (`test_linkedin_compat` → new endpoint semantics).
- New repo test: latest-by-version for `original_*` and `linkedin_*`.

Frontend (`cd apps/frontend && npx vitest run`):

- `ResumeTab.test.tsx`: mock `global.fetch` — upload resume/linkedin posts
  `{raw_text}` and handles `{status:'saved', version}`; delete calls the API
  with the row `id`.

---

# Important Constraints

- All DB access via SQLAlchemy repository (AGENTS.md rule 2); no raw SQL.
- All AI calls go through LLMService (rule 1) — this change only edits prompts.
- No new routes in `entrypoints/api.py`; use per-context routers (rule 10).
- `mask_pii` is applied on save (matches existing UI privacy copy).
- Keep `build_resume_text` for backward compatibility (may be unused by nodes).
- Do not change the job analysis output schema; only bump the prompt version.
- LinkedIn is added to **scoring only** — resume/cover generation stays resume-only.
