# Prompt 087 - Fix LLM Context Bloat: Thin Data Into LLM

## Objective

Company/job analysis prompts reach 200 KB+ because the extracted content
passed to the LLM is mostly JavaScript/Next.js RSC noise (the failing Cara
Care session had a 175 KB company content block — ~87% of the prompt). The
small model then truncates/malforms the response JSON. Two defects combine:

1. **No extractor installed** — `trafilatura`, `beautifulsoup4` and
   `playwright` are absent from `pyproject.toml`, so `CompositeContentExtractor`
   always lands on the raw regex `_fallback` which strips HTML tags but keeps
   the full `<script>` bodies (RSC payloads, `dataLayer`, gtag).
2. **No input budget** — extracted sources flow into `combined_text` uncapped.
   Jobs cap resume/LinkedIn at `MAX_PROFILE_DOC_CHARS = 6000`
   (`job_analysis_inputs.py`), but sources had no per-source or total cap.

Goal: feed thin, concise, trimmed data into the LLM so the prompt stays small
and the model stops truncating output.

## Current State

- `processing/infrastructure/content/extractors/__init__.py`:
  `CompositeContentExtractor._fallback` only strips tags via
  `re.sub(r"<[^>]+>", " ", ...)` — script bodies survive.
- `CompanyContextBuilderService.build` / `JobContextBuilderService.build`
  concatenate each source's `clean_text` into `combined_text` with no cap.
- `beautifulsoup4` was not a dependency (optional import guarded by
  `ImportError` in `bs4_extractor.py`).

## Implementation Steps

1. Add `beautifulsoup4>=4.12` to `pyproject.toml` dependencies and `uv sync`.
   This activates the existing `BeautifulSoupContentExtractor` (already
   decomposes `script`/`style`/`noscript`), which becomes the effective
   extractor (trafilatura still optional).
2. Harden `CompositeContentExtractor._fallback` (safety net when no extractor
   works): strip non-content element bodies
   (`script|style|noscript|head|iframe|template|svg|math`) via regex, collapse
   whitespace, and cap the output at `MAX_FALLBACK_CHARS = 40_000`.
3. New `processing/application/services/context_budget.py`:
   - `MAX_SOURCE_CHARS = 8_000` (per extracted source)
   - `MAX_COMBINED_CHARS = 48_000` (total `combined_text`)
   - `trim_text(text, max_chars, keep_head=True)` — keeps head, appends a
     `[truncated]` marker, option to keep the tail instead.
4. Apply caps in both `CompanyContextBuilderService.build` and
   `JobContextBuilderService.build`: trim each source to `MAX_SOURCE_CHARS`,
   then trim the joined text to `MAX_COMBINED_CHARS`.
5. Tests:
   - `test_context_budget.py` — trim_text behavior + constants.
   - `TestCompositeFallback` — JS/RSC bodies stripped, whitespace collapsed,
     fallback capped.
   - builder tests — oversized source and oversized combined totals are
     trimmed and marked `[truncated]`.

## Testing Requirements

- `uv run pytest apps/backend/tests/processing/application/test_context_budget.py
  apps/backend/tests/processing/application/test_job_context_preparation.py
  apps/backend/tests/processing/application/test_company_context_preparation.py -v`
  — all green.
- Full backend suite: `uv run pytest apps/backend/tests/ -v`.
- Manual sanity: a JS-heavy Next.js page through `CompositeContentExtractor`
  returns clean text (verified: 175 KB → 271 chars, no `$undefined`/`dataLayer`).

## Constraints

- Code-only fix — no data migration or notes/links cleanup (notes are at most
  ~18 KB in the DB; the bloat is scraped `raw_content`, not stored notes).
- Keep behavior change minimal: same prompts/schema; only the input data and
  its size change.
- SemVer PATCH bump to **3.5.3** in all version locations (`VERSION`,
  `CHANGELOG.md`, `pyproject.toml`, `apps/frontend/package.json`) and tag
  `v3.5.3`; `./scripts/check-version.sh` must pass.
- Update `docs/workflows/job-processing.md` and
  `docs/ai/job-processing-context.md` to document extraction and the budget.
