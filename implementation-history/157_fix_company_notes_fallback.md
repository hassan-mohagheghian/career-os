# Prompt 157 - Company processing: notes fallback when all links produce no content

## Objective

Ensure a company whose links error out (no content extracted) can still process
successfully when it has notes. If **all** links yield no content, at least one
note must be provided — otherwise the run must fail with a clear, actionable
reason.

## Current State

- `CompanyContextValidatorService` (`company_context_validator.py`) already
  treats a context as valid when `bool(meaningful_extracted or meaningful_notes)
  and bool(context.sources)`, so notes are already a sufficient fallback.
- However the failure reasons were generic (`no extracted content`, `empty
  notes`), the behavior had no explicit company-level test coverage, and no doc
  described it.
- Concrete case: company `01a003cf-58c0-772d-8286-aacf2ba01736` (A2G) has empty
  `notes` and a website that yields no content, so it failed with
  `[validate_context] no extracted content; [validate_context] empty notes`.

## Changes

- `apps/backend/processing/application/services/company_context_validator.py`:
  when there is no extracted content **and** no notes, report a single clear
  reason: `no extracted content and no notes — at least one note is required
  when links produce no content`. Otherwise keep the granular reasons.

## Testing Requirements

- Add to `apps/backend/tests/processing/application/test_company_context_preparation.py`
  (graph-level, mirroring the real company):
  - `test_all_links_fail_but_note_present_is_valid` — all sources fail to fetch
    but a text note exists → `COMPLETED`, valid, combined text is the note, and
    the "note required" reason is absent.
  - `test_all_links_fail_without_note_requires_note` — all sources fail and no
    notes → `FAILED`, invalid, reason mentions "at least one note is required".
- Run:
  `uv run pytest apps/backend/tests/processing/application/test_company_context_preparation.py -q`
- Live verification (read-only): load A2G via the real repo; run
  `CompanyContextPreparationGraph` with a failing fetcher. Empty notes → failed
  with the "at least one note is required" reason; one text note → completed/valid.

## Docs

- `docs/ai/graphs.md`: document the company context preparation graph and the
  notes-fallback validation rule.

## Constraints

- No schema/migration change; validator message only. Respect AGENTS.md 2
  (implementation history first), 16 (no new event needed).
