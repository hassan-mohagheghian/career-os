# Prompt 175 - Placeholders page and PDF download

## Objective

Add a Placeholders feature so the user stores personal details (`{{token}}`
values) once on a new page and downloads each generated resume / cover letter as a
filled **PDF**. The workspace document cards gain a "Download PDF" action backed by
a new backend PDF endpoint.

## Current State

- Backend contexts are per-router and decoupled (rule 10, 15); generated documents
  live in `apps/backend/applications/...` (content stored as markdown, served via
  the applications router). No placeholder/substitution mechanism exists.
- The frontend workspace documents card is
  `apps/frontend/src/features/job-application/components/ApplicationDocuments.tsx`
  (per-document actions: preview, copy, `.md` download, edit, delete, generate).
  The http client is `apps/frontend/src/shared/api/http-client.ts` (`api.get/post/...`,
  JSON only, no blob download helper).
- Nav items: `apps/frontend/src/widgets/sidebar/nav-items.ts` (`NAV_ITEMS`); pages
  are FSD widgets under `apps/frontend/src/widgets/<name>/index.tsx` reached via a
  `app/<name>/page.tsx` route. Placeholder-key labels/values are authored in a new
  `placeholders` bounded context.
- DB migration flow is autogenerate-then-tune (AGENTS.md rule 14); head is
  `application_005` (status rename). The `placeholders` schema is brand new.

## Changes

Backend (new bounded context `apps/backend/placeholders/`):
- Domain: `Placeholder` + `PlaceholderKey` catalog (`ALL`, `LABELS`), token
  substitution `fill_placeholders(content, values)` (case-insensitive, unknown
  tokens left intact) in `domain/entities/placeholder.py`; `PlaceholdersUpdated`
  event in `domain/events.py`; publisher port + in-memory collector in
  `domain/event_publisher.py` (EDD rule 16).
- Infrastructure: SQLAlchemy `PlaceholderModel` (`key` PK, `value`), SA repository.
- Application: `PlaceholderService` (`list`, `get_map`, `upsert_many`, `fill`,
  `keys`) emitting the event best-effort.
- Presentation: `GET /api/placeholders` (keys+labels, items, values) and
  `PUT /api/placeholders` (upsert flat `{key:value}`) in
  `presentation/api/placeholders_router.py`; wire deps in `apps/backend/dependencies.py`
  and register under `/placeholders` in
  `apps/backend/shared/presentation/api/root_router.py`.
- Migration: `placeholder_001_initial_placeholders_schema` (down_revision
  `application_005`, branch `placeholders`); add model import + schema to
  `sqlalchemy_config.SCHEMAS` and `alembic` `env.py`.

Backend (PDF):
- Add `markdown` + `fpdf2` deps to `pyproject.toml`; create
  `shared/infrastructure/pdf_renderer.py` (`MarkdownPdfRenderer.render(content, title)` → PDF bytes).
- In `applications_router.py`: inject `get_placeholder_service`; fill document
  content server-side via a `_fill_documents` helper in by-job/create/update/detail
  responses; add `GET /api/applications/documents/{document_id}/pdf` returning
  `application/pdf` with `Content-Disposition: attachment`.
- In `processing/.../application_intelligence_prompts.py`: instruct the LLM to emit
  `{{name}}, {{title}}, {{email}}, {{phone}}, {{location}}, {{linkedin}}, {{github}}`
  contact tokens in header/signature blocks only (literal tokens via a
  `CONTACT_PLACEHOLDERS` constant, since the prompt is an f-string).

Frontend:
- `src/entities/placeholders/{types,api,hooks}.ts` (list/update + usePlaceholders).
- `src/widgets/placeholders-page/index.tsx` + `app/placeholders/page.tsx` (labeled
  form per canonical key, Save → `PUT`, success toast, dirty buffer).
- Add `placeholders` nav item (icon `TextT`) to `src/widgets/sidebar/nav-items.ts`.
- Add `api.download` (blob fetch) to `src/shared/api/http-client.ts`; add
  `applicationApi.downloadPdf(documentId, filename)` and
  `useDownloadDocumentPdf` hook.
- `ApplicationDocuments.tsx`: add a "Download as PDF" button (spinner while pending).

## Testing Requirements

- `apps/backend/tests/placeholders/`: service (substitution, upsert idempotence,
  event, fill) and router (list/update/overwrite) tests.
- `apps/backend/tests/applications/.../test_applications_router.py`: document detail
  substitutes placeholders; `GET .../pdf` returns `application/pdf` starting `%PDF`
  with a filename; missing document → 404.
- `apps/backend/tests/shared/infrastructure/test_pdf_renderer.py`: render returns
  valid PDF bytes.
- `apps/backend/tests/processing/.../test_application_intelligence.py`: prompts
  contain `{{name}}`/`{{email}}`/`{{linkedin}}` and `PLACEHOLDERS`.
- Frontend: `entities/placeholders/api.test.ts`; `ApplicationDocuments.test.tsx`
  (PDF button present when doc exists, absent when not); `api.test.ts` downloadPdf.
- Register the placeholders model in `apps/backend/tests/conftest.py`.
- Run `uv run pytest apps/backend/tests/ -v` (excluding pre-existing
  `test_repository_extra.py`) and `cd apps/frontend && npx vitest run` +
  `npm run typecheck`.

## Constraints

- No cross-context FKs (rule 15): placeholders are standalone; documents reference
  tokens by name only. No raw SQL (rule 2). Alembic autogenerate then tune (rule 14).
- UI changes ship with wireframe docs (rule 13): new
  `docs/ux/features/placeholders/placeholders.md`, updated
  `docs/ux/README.md` index, `docs/ux/DESIGN.md`, and applications documents UX +
  API docs for the PDF endpoint.
- Document events in `docs/domain/placeholders/{placeholders,events}.md` (rule 16).
- Keep `VERSION`/version files untouched (no release bump requested).