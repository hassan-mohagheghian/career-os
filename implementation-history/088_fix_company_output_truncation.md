# Prompt 088 - Fix Company Analysis Output Truncation

## Objective

Company analysis still fails with `Failed to parse opencode JSON output` even
after the input-side fix (Prompt 087) slimmed the context. The remaining
failure is on the **output** side: the full combined company-analysis JSON
(extraction + 7 intelligence sections + recommendation + scores ≈ 100+ fields)
needs ~2,559 output tokens (≈ 11,154 chars), but the `deepseek-v4-flash-free`
model caps output around ~2.7K tokens. A complete reply sits right at/over the
ceiling, so the model truncates the JSON structurally (extra top-level object,
or an unclosed tail) and `OpencodeProvider._extract_json` cannot repair it.

Goal: shrink the combined output contract so a complete, valid JSON fits well
under the model's output window.

## Current State

- `apps/backend/companies/infrastructure/ai/prompts/company/company_combined_analyze.txt`
  enumerates ~100 output fields with verbose per-field guidance and generous
  size limits (`description` ≤120 words, explanations ≤40 words, factor lists
  ≤4 items).
- Measured valid output: total 11,154 chars — `intelligence` alone 6,385 chars
  (57%), of which `overview`/`culture_analysis`/`visa_analysis` duplicate
  extraction fields.
- Failing sessions show `output` tokens 2259–2683 with broken JSON:
  `ses_028f167d0ffe` (extra data), `ses_028eb77d8ffe` ("Expecting ',' delimiter").
- The JSON schema, validation model, persistence and scoring all treat the
  intelligence sections as open dicts (`additionalProperties: True` /
  `dict[str, Any]`), so the enumerated sub-fields live only in the prompt
  template. The frontend (`CompanyDetailDrawer.tsx`) reads a subset of these
  sub-fields and renders missing ones as empty.

## Implementation Steps

1. Tighten the template's OUTPUT SIZE LIMITS:
   - `extraction.description`: ≤50 words.
   - every explanation field: ≤15 words.
   - factor/risk/positive-signal lists: ≤3 items each.
   - total JSON under ~1600 words.
2. Add a no-duplication instruction: intelligence must add NEW insight, not
   restate extraction facts (overview no longer repeats `description`).
3. Drop low-value / un-rendered intelligence sub-fields:
   - `culture_analysis`: drop `environment`, `innovation`, `engineering_blog`.
   - `benefits_analysis`: drop `salary_info`, `equity`, `pension`,
     `health_insurance`, `relocation`.
   - `overview`: drop `description` (frontend uses `company.description`).
   - `technology_analysis`: shorten field guidance.
4. Keep the schema (`build_company_analysis_output_schema`), validation model
   (`CompanyCombinedAnalysisOutput`), persistence and scoring unchanged — they
   are open/lenient dicts.
5. Tests (`apps/backend/tests/processing/application/test_company_analysis.py`,
   new `TestCompanyAnalysisPrompt`):
   - prompt contains the tightened limits (≤50/≤15/≤3, ~1600 words).
   - prompt contains the no-duplication instruction.
   - dropped sub-fields absent from the prompt; rendered fields still present.

## Testing Requirements

- `uv run pytest apps/backend/tests/processing/application/test_company_analysis.py -v`
  — all green.
- Full backend suite: `uv run pytest apps/backend/tests/ -v`.
- Manual: pipe the built prompt through
  `opencode run --format json --dangerously-skip-permissions` → complete valid
  JSON, output ≈ 1,084 tokens (well under the cap), `reason: stop`.

## Constraints

- Bug fix → SemVer PATCH bump to **3.5.4** in all version locations
  (`VERSION`, `CHANGELOG.md`, `pyproject.toml`, `apps/frontend/package.json`)
  and tag `v3.5.4`; `./scripts/check-version.sh` must pass.
- No schema/validation/persistence/scoring changes — output structure keys stay
  identical; only prompt guidance and per-field size limits change.
- Update `docs/ai/prompts.md` (company combined analysis section).
