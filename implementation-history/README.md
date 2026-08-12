# implementation-history

A sequential, human-readable ledger of every implementation task in this repo.
Each file is a **self-contained implementation prompt** for that task, written
before any code is written (AGENTS.md Development Workflow, step 2). Think of it
as the "why + how" archive of the codebase.

**Audience:** AI agents preparing to make a change, and humans reviewing what
was done and why.

---

## File naming

```
NNN_scope_title.md
```

| Part    | Rule                                                                                |
| ------- | ----------------------------------------------------------------------------------- |
| `NNN`   | Next sequential number (highest existing + 1), 3-digit padded (`062`, `143`).       |
| `scope` | One of `feature`, `refactor`, `fix`, `chore`, `docs`, `ux`.                         |
| `title` | Short `snake_case` summary of the change.                                           |

Examples: `143_feature_recruiter_row_tint.md`, `142_refactor_move_frontend_features_to_v2.md`.

> Note: early entries (≤ 099) used inconsistent scopes or none (e.g.
> `001_company_page.md`). New files **must** follow the `NNN_scope_title` rule.

---

## Template

Every prompt follows the same skeleton, in this order, with **plain
`##` headers**:

```markdown
# Prompt NNN - <Title>            (human sentence case, matches the file title)

## Objective                       1–3 sentences: what changes and why.

## Current State                   Facts about today's code, not a plan.
                                   Reference exact file paths + line numbers.

## Changes                         Concrete, ordered edit list. Name files, hooks,
                                   components, routers, schemas, migrations.

## Testing Requirements            Test files to add/update and commands to run.

## Constraints                     Architecture rules to respect (no cross-context
                                   FKs, no raw SQL, docs-first, ...).
```

See `061_processing_drawer_action_buttons.md` for a fully worked example.

---

## Token-efficiency rules (for AI agents)

These rules exist to keep the ledger useful **without blowing up context
windows**. Read this section before creating or reading a prompt.

1. **Keep each prompt focused.** Aim for the size of `061`–`143` (roughly
   20–60 lines). If a task needs more, split it into multiple sequential prompts.
2. **Never copy file contents into a prompt.** Reference the file by path
   (`apps/frontend/src/entities/processing/api.ts`) and cite what matters
   (`ProcessingDrawer.tsx:31`). Agents can read the file themselves.
3. **Don't paste docs.** Point to the doc path (`docs/api/processing/cancel-processing.md`)
   instead of quoting it.
4. **Never paste the whole repo state.** `## Current State` lists only the
   files/tables/routes relevant to *this* change.
5. **Don't restate AGENTS.md.** It is already in every agent's context; write
   "respect AGENTS.md rule N" instead of re-explaining the rule.
6. **When reading the ledger, read selectively.** Search/read only the prompts
   that touch the same modules (`grep` for the feature path or scope), not the
   entire folder. Do not load the full `implementation-history/` directory into
   context.
7. **One number, one file.** Each prompt is a single self-contained change. Never
   reuse a number, and never let one prompt describe two unrelated changes.
8. **Facts over prose.** Bullet lists, exact paths, and endpoint names beat
   paragraphs. No fluff, no filler sentences.
9. **Do not link-format.** Keep the file plain Markdown with only the `##`
   section headers listed in the template.

---

## Workflow

1. **Investigate** the relevant docs and code (AGENTS.md step 1).
2. **Create the prompt file** here with the next number — this is
   non-negotiable before any code is written.
3. **Write tests + update docs first** (TDD red phase).
4. **Implement** (TDD green phase).
5. **Commit** the prompt file together with the code change.
