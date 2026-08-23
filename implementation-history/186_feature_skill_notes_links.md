# Prompt 186 - Skill Notes & Links

## Objective

Add notes and links to the Skills bounded context so users can track their learning progress, save documentation URLs, and maintain personal study resources for each skill. Links have a title (for web pages, tutorials, docs), notes are free-text activity entries.

## Current State

- Skills have no notes or links infrastructure.
- The application notes pattern (`application_notes` table + `INoteRepository` + `NoteService`) is the closest reference pattern.
- The `SkillDetailDrawer` displays read-only skill info but has no user-editable content sections.
- The skill schema has 6 existing tables: `skills`, `skill_aliases`, `skill_categories`, `skill_category_links`, `skill_breakdowns`, `skill_relationships`, `skill_mentions`.

## Implementation Steps

### 1. Migration (backend)

Create `apps/alembic/skill/versions/skill_003_add_notes_and_links.py`:
- `down_revision = "20fc9eceffce"` (current head of skill schema)
- Create `skill.skill_notes` table: `id` (UUID PK), `skill_id` (FK→skill.skills.id), `content` (Text), `created_at` (Text), `updated_at` (Text)
- Create `skill.skill_links` table: `id` (UUID PK), `skill_id` (FK→skill.skills.id), `title` (String, not null), `url` (String, not null), `created_at` (Text)
- Index on `skill_id` for both tables

### 2. ORM Models (backend)

Add to `apps/backend/skills/infrastructure/models/skill_model.py`:
- `SkillNoteModel`: columns `id`, `skill_id` (FK→skill.skills.id), `content`, `created_at`, `updated_at`
- `SkillLinkModel`: columns `id`, `skill_id` (FK→skill.skills.id), `title`, `url`, `created_at`
- Add `notes` and `links` relationships to `SkillModel`

### 3. Domain repository interfaces (backend)

Create `apps/backend/skills/domain/repositories/skill_note_repository.py`:
- `ISkillNoteRepository`: `create(data)`, `list_for_skill(skill_id)`, `get_by_id(note_id)`, `delete(note_id)`

Create `apps/backend/skills/domain/repositories/skill_link_repository.py`:
- `ISkillLinkRepository`: `create(data)`, `list_for_skill(skill_id)`, `get_by_id(link_id)`, `delete(link_id)`

### 4. Infrastructure repositories (backend)

Create `apps/backend/skills/infrastructure/repositories/sa_skill_note_repository.py`:
- `SQLAlchemySkillNoteRepository(ISkillNoteRepository)`

Create `apps/backend/skills/infrastructure/repositories/sa_skill_link_repository.py`:
- `SQLAlchemySkillLinkRepository(ISkillLinkRepository)`

### 5. Mappers (backend)

Add to `apps/backend/skills/infrastructure/mappers.py`:
- `skill_note_model_to_dict(model)` → `{id, skill_id, content, created_at, updated_at}`
- `dict_to_skill_note_model(data)` → `SkillNoteModel`
- `skill_link_model_to_dict(model)` → `{id, skill_id, title, url, created_at}`
- `dict_to_skill_link_model(data)` → `SkillLinkModel`

### 6. Service (backend)

Create `apps/backend/skills/application/services/skill_resource_service.py`:
- `SkillResourceService(note_repo, link_repo, skill_repo)`:
  - `add_note(skill_id, content)` → validates skill exists + non-empty, creates note, returns dict
  - `delete_note(note_id)` → deletes note
  - `add_link(skill_id, title, url)` → validates skill exists + non-empty title+url, creates link, returns dict
  - `delete_link(link_id)` → deletes link

### 7. API schemas (backend)

Add to `apps/backend/skills/presentation/api/schemas/skills.py`:
- `CreateSkillNoteRequest(content: str)` with validator
- `SkillNoteSchema(id, skill_id, content, created_at, updated_at)`
- `CreateSkillLinkRequest(title: str, url: str)` with validators
- `SkillLinkSchema(id, skill_id, title, url, created_at)`
- Add `notes: list[SkillNoteSchema]` and `links: list[SkillLinkSchema]` to `SkillListItemSchema` (optional, default [])

### 8. API router (backend)

Add to `apps/backend/skills/presentation/api/skills_router.py`:
- `POST /{id}/notes` → `add_skill_note` (201)
- `DELETE /notes/{note_id}` → `delete_skill_note` (204)
- `POST /{id}/links` → `add_skill_link` (201)
- `DELETE /links/{link_id}` → `delete_skill_link` (204)
- Enhance `get_skill` to include notes and links from repos

### 9. Dependencies (backend)

Add to `apps/backend/dependencies.py`:
- `get_skill_note_repo(session)` → `SQLAlchemySkillNoteRepository`
- `get_skill_link_repo(session)` → `SQLAlchemySkillLinkRepository`
- `get_skill_resource_service(note_repo, link_repo, skill_repo)` → `SkillResourceService`

### 10. Frontend types

Add to `apps/frontend/src/entities/skill/types.ts`:
- `SkillNote { id, skill_id, content, created_at, updated_at }`
- `SkillLink { id, skill_id, title, url, created_at }`
- Add `notes?: SkillNote[]` and `links?: SkillLink[]` to `Skill` type

### 11. Frontend API

Add to `apps/frontend/src/entities/skill/api.ts`:
- `skillApi.addNote(skillId, { content })`
- `skillApi.deleteNote(noteId)`
- `skillApi.addLink(skillId, { title, url })`
- `skillApi.deleteLink(linkId)`

### 12. Frontend hooks

Add to `apps/frontend/src/entities/skill/hooks.ts`:
- `useAddSkillNoteMutation()` — invalidates skill query
- `useDeleteSkillNoteMutation()` — invalidates skill query
- `useAddSkillLinkMutation()` — invalidates skill query
- `useDeleteSkillLinkMutation()` — invalidates skill query

### 13. Frontend component

Create `apps/frontend/src/features/skills-v2/components/SkillResources.tsx`:
- Two sections: "Notes" and "Links"
- Notes: list of notes with DateTime + delete button (hover reveal), textarea input with Add Note button
- Links: list of links with title (clickable to open URL), delete button, input row with title + url + Add Link button
- Uses `useSkillDetailQuery` or accepts skill as prop
- Wire into `SkillDetailDrawer` between Tags and Referenced Jobs sections

### 14. Tests (backend)

Add tests in `apps/backend/tests/skills/`:
- Test `POST /{id}/notes` creates note
- Test `DELETE /notes/{note_id}` deletes note
- Test `POST /{id}/links` creates link
- Test `DELETE /links/{link_id}` deletes link
- Test `GET /{id}` returns notes and links
- Test 404 for missing skill

### 15. Tests (frontend)

Add test for `SkillResources` component:
- Renders notes list
- Renders links list
- Add note form works
- Add link form works

### 16. Docs

- Create `docs/ux/features/skills/skill-resources.md` (wireframe + Mermaid)
- Update `docs/ux/features/skills/page.md` if exists
- Update `docs/ux/README.md`

## Constraints

- Notes and links live in the `skill` schema (same bounded context as skills).
- FKs are within the skill context only (rule 15).
- Notes are free-text, immutable (no edit, only add/delete).
- Links always have a title + URL.
- Follow the application notes pattern (`INoteRepository` / `NoteService`) closely.
- Default sort: notes and links newest first.
- Tests first (TDD red phase), then code.
