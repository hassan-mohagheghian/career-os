# Prompt 080 - Fix Company Scores Null After Processing

## Objective

Company analysis was persisting **null numeric scores** (fit/success/overall)
while keeping the explanation/factor text. Root cause: a key-name mismatch in
the scoring pipeline. The LLM contract and read paths used two different key
sets (`company_fit_score` / `company_success_score` / `company_overall_score`
vs. `fit` / `success` / `overall`), and `build_company_analysis_result` read
the legacy keys that the validated payload no longer carries.

This change **unifies the score keys to the canonical form**
(`fit` / `success` / `overall`) everywhere and **removes the legacy keys**
from the LLM contract, validation, scoring, API read path, frontend, stored
data, and docs.

## Current State

- `AnalyzeCompanyNode` persists `CompanyCombinedAnalysisOutput.model_dump()`
  into `analysis_context["raw_payload"]`. `CompanyScores.map_legacy_keys`
  renames `company_fit_score` → `fit` (etc.) and `model_dump()` emits only the
  canonical keys, so the legacy keys no longer exist after validation.
- `ScoreCompanyNode` → `build_company_analysis_result` read
  `scores_raw.get("company_fit_score")` / `get("company_success_score")` →
  always `None` → `fit`/`success`/`overall` = `None`, grades `"P"`, while the
  explanation text passed through. Every company processed via the new
  `COMPANY_PROCESSING` workflow (status `processed`) stored null scores.
- The API (`companies_v2_router._score_aliases`, `SCORE_KEY_MAP`) and frontend
  (drawer fallbacks) carried the legacy keys to mask the mismatch.
- The `26` pre-workflow rows (status `completed`) store legacy-only keys and
  would break once the read path dropped the legacy handling — a data
  migration is required.

## Implementation Steps

### Write path (the bug fix)

1. `processing/application/services/company_analysis_scoring.py`:
   `build_company_analysis_result` reads `scores_raw.get("fit")` /
   `get("success")`; `fit_grade = grade_for_overall(fit)`; the three
   `company_*_score` aliases are removed from the output dict.

### LLM contract → canonical

2. `companies/infrastructure/ai/prompts/company/company_combined_analyze.txt`:
   example JSON, scoring-guideline headers and the `overall` formula use
   `fit` / `success` / `overall`.
3. `processing/application/services/company_analysis_prompt.py`: schema
   properties → `fit` / `success` / `overall`; bump
   `COMPANY_ANALYSIS_PROMPT_VERSION` and `COMPANY_ANALYSIS_SCHEMA_VERSION`
   → `1.1.0`.
4. `processing/application/services/company_analysis_validation.py`: remove
   `CompanyScores.map_legacy_keys` (and the now-unused `model_validator`
   import).
5. `processing/application/workflows/company_analysis/nodes/analyze_company_node.py`:
   `_RETRY_SHORTEN_HINT` → `scores (fit, success)`.

### Read path → canonical only

6. `companies/presentation/api/companies_v2_router.py`: `SCORE_KEY_MAP` →
   `{overall_score: overall, fit_score: fit, success_score: success}`;
   delete `_score_aliases`; list/detail/sort read
   `scores.get("overall")/("fit")/("success")`.

### Data migration

7. `alembic/company/versions/company_006_normalize_intelligence_score_keys.py`:
   rewrite every `company_intelligence.scores` JSON to map
   `company_fit_score` → `fit`, `company_success_score` → `success`,
   `company_overall_score` → `overall` (only where the canonical key is
   missing) and drop the legacy keys. Applied via `alembic upgrade head`.

### Frontend

8. `entities/company/types.ts`: `CompanyIntelligenceScores` → canonical
   optional fields.
9. `features/companies-v2/components/CompanyDetailDrawer.tsx`: remove the
   `company_*_score` fallbacks (use `rawScores.fit/success/overall`).
10. `features/companies-v2/components/CompanyDetailDrawer.test.tsx`: mock
    intelligence scores → canonical keys.

### Tests

11. `tests/processing/application/test_company_analysis.py`:
    - `_valid_payload()`, the clamping test and scoring assertions → canonical
      keys; assert no `company_*_score` keys in the result.
    - **New** `test_validated_payload_scores_survive_round_trip`: raw payload →
      `model_validate().model_dump()` → `build_company_analysis_result()` must
      keep the scores (the exact production path that was broken).
    - **New** `test_scores_survive_analyze_then_score_chain`: chained
      `AnalyzeCompanyNode` → `ScoreCompanyNode` produces non-null scores.
12. `tests/companies/presentation/api/test_companies_v2_api.py`: seed intel and
    `_processed_scores()` with canonical keys; assert `intelligence.scores` is
    canonical-only.

### Docs

13. `docs/api/companies/list-companies.md` (scores blob + score-sort keys),
    `docs/api/companies/company-detail.md` (response example),
    `docs/ux/features/companies/company-detail.md` (score source wording).

## Testing Requirements

- Backend: `uv run pytest apps/backend/tests/` — 1221 passed.
- Frontend: `cd apps/frontend && npx vitest run` — 377 passed.
- Migration applied on the live dev DB; no row regressed (the 7 older
  `visa_score`-shaped rows never carried score keys and stay unchanged).

## Constraints

- All AI calls go through `LLMService`; no providers called directly.
- No version change in only one place — bump via `VERSION` / `CHANGELOG.md` /
  `pyproject.toml` / `apps/frontend/package.json`, then `check-version.sh`.
- Release as PATCH **3.3.1** (bug fix + internal key unification; no public
  API shape change).
