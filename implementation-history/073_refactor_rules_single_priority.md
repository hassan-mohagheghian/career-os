# Prompt 073 - Single Rule Priority + Complete Rules UX Docs

## Objective

Collapse the two rule scoring fields (`priority` and `score_weight`) into a
single `priority` that drives list order, the severity badge, and the LLM
weight. Move up/down reorders rules relative to their neighbors (`neighbor ± 1`,
clamped 0–100) while keeping drag-and-drop. Document the Rules page and its
Add/Edit drawer completely with wireframes, and add the standing "wireframe
docs for every UI change" rule to AGENTS.md.

## Current State

- Rules had both `priority` and `score_weight` columns; the UI showed a `w:N`
  weight from `score_weight`, and Move up/down buttons stepped priority by ±5.
- Drag-and-drop redistributed priorities linearly (100→1).
- The Rules page and Rule drawer had **no** docs under `docs/ux/features/` or
  `docs/ux/flows/`; AGENTS.md had no wireframe-doc rule.

## Implementation Steps

1. Backend — remove `score_weight` from the model, domain entity, repository
   (`_to_dict`, `create`, `update`, `bulk_update`), seed data, CLI
   (`rules` list + `add_rule` option), AI DB tool (`database.py` returns
   `priority` instead), and all LLM text builders (weight = `priority`).
2. Migration — `apps/alembic/shared/versions/shared_003_remove_score_weight.py`
   (down_revision `job_004_merge_job_heads`) drops the column; verified on a
   throwaway DB and applied to the dev DB.
3. Frontend — `RulesTab.tsx`: `w:{priority}` label; Move up =
   `min(preceding.priority + 1, 100)`, Move down = `max(following.priority − 1,
   0)`, no-op at edges; drag kept. `RuleFormDrawer.tsx`: Priority (0-100) input;
   save sends `priority` in add and edit.
4. Docs — `docs/ux/features/rules/page.md` (wireframe, badge legend, reorder),
   `docs/ux/features/rules/rule-form-drawer.md` (drawer wireframe), and
   `docs/ux/flows/rules/reorder-rules.md`; update `docs/ux/README.md`,
   `DESIGN.md` (Rules page + drawer wireframes), `docs/api/api-design.md`
   (rules endpoints + payload), `DOMAIN.md` (Scoring Rules), and
   `docs/architecture/bounded-context-analysis.md` (ScoringRule fields).
5. AGENTS.md — add non-negotiable rule 13: every UI change must ship with
   wireframe docs under `docs/ux/` and stay in sync with `docs/ux/README.md`
   and `DESIGN.md`.

## Testing Requirements

- Frontend: rules tests cover move up (preceding + 1), move down (following − 1),
  lone-rule no-op, `w:{priority}` label, and drawer priority editing.
- Backend: CLI `w:` output uses priority; rule worker/stream tests construct
  rules without `score_weight`; seed count unchanged.
- Migrations apply cleanly on a fresh DB.

## Constraints

- Priority stays within 0–100.
- No UI change ships without its ASCII-wireframe doc (AGENTS.md rule 13).
