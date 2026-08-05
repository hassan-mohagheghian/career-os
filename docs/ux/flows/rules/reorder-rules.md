# Reorder Rules Flow

## Goal

Change the order in which scoring rules are applied — and therefore their
severity — using either the Move up / Move down buttons or drag-and-drop.

## Model

Every rule has a single **priority** (0–100):

- **Order**: rules sort by `priority` descending (highest first).
- **Badge**: derived from priority (≥90 Critical, ≥75 High, ≥50 Med, else Low).
- **Weight**: priority is serialized as `w:{n}` into LLM scoring prompts.

Reordering a rule changes only its `priority`.

---

## Flow 1 — Move up / Move down buttons

```text
Start: [A Critical w:100] [B High w:80] [C Med w:60]

1. Hover rule C → actions appear → click ↓ / ↑
2. C moves one step; C.priority = neighbor ± 1
   ↑ on C:  C = B.priority + 1 = 81        → [A w:100] [C w:81] [B w:80]
   ↓ on C:  C = B.priority − 1 = 79        → [A w:100] [B w:80] [C w:79]
3. List refetches and re-sorts; only C changed
```

Rules:

- **Move up**: `priority = min(preceding.priority + 1, 100)`
- **Move down**: `priority = max(following.priority − 1, 0)`
- No-op at the edges (first rule cannot move up; last rule cannot move down).
- Neighbors keep their values; only the moved rule is written.

### Edge cases

| Situation                          | Result                                                        |
| ---------------------------------- | ------------------------------------------------------------- |
| Rule already first in column       | Move up does nothing                                          |
| Rule already last in column        | Move down does nothing                                        |
| Preceding rule at priority 100     | Moved rule clamps to 100 (may tie with its neighbor)          |
| Following rule at priority 0       | Moved rule clamps to 0 (may tie with its neighbor)            |

---

## Flow 2 — Drag-and-drop

```text
1. Grab the ⠿ handle of a rule
2. Drag it above/below another rule in the same column
3. On drop the column recomputes priorities across ALL rules,
   redistributed from 100 down to 1 (within 0–100)
4. List refetches and re-sorts
```

Drag reordering always stays within 0–100 by construction (it distributes the
range across the column). It is the only action that rewrites more than one
rule at a time.

---

## Outcome

After either flow the priority/badge/weight all stay consistent because they
share the single `priority` value. The new order is persisted and used on the
next job / company scoring run.
