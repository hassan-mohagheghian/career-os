# Flow: Create a Manual Roadmap

## Goal

Create a new learning/job-preparation roadmap from scratch (no AI), set its goal,
and start adding milestones and tasks on the detail page.

## Actors & Entry

- **Actor**: signed-in user.
- **Entry**: `/roadmaps` →

## Steps

```mermaid
flowchart TD
    A["My Roadmaps page"] --> B["Click ➕ New Roadmap"]
    B --> C["Dialog: enter Title (required), Description (optional), Goal (optional)"]
    C -->|"Create disabled until title present"| D["Click Create"]
    D -->|"POST /api/roadmaps {source implicit MANUAL}"| E["Toast 'Roadmap created'; list refetches; card appears"]
    E --> F["Click Open on the card"]
    F --> G["Roadmap detail (empty: No milestones yet)"]
    G --> H["Click Add Milestone → dialog → Add"]
    H --> I["Milestone node appears"]
    I --> J["Click Task inside milestone → dialog → Add"]
    J --> K["Task row appears; check off to progress"]
```

## Wireframe of key screens

```text
/roadmaps (list):
  [My Roadmaps]                  [ ➕ New Roadmap]
  ┌───────────────────────────┐
  │ 🗺 My New Roadmap          │
  │ Goal: CUSTOM              │
  │ [MANUAL][ACTIVE] 0/0 · 0% │
  │ [Open] [✎] [🗑]           │
  └───────────────────────────┘

/roadmaps/{id} (after add milestone/task):
  [← My Roadmaps]
  🗺 My New Roadmap
  JOURNEY                                [+ Add Milestone]
  ┌ ① Foundation ──────────┐
  │ ☐ First task · MEDIUM   │
  └─────────────────────────┘
```

## Edge Cases

| Case | Behavior |
| ---- | -------- |
| Title empty | Create button stays disabled |
| Create fails | Error toast; dialog remains open |
| Duplicate titles | Allowed (no uniqueness) |
| Long text | Inputs wrap; card title truncates |
| Cancel | Dialog closes without creating |

# Related Documents

- `docs/ux/features/roadmaps/roadmap-create-edit.md`
- `docs/ux/features/roadmaps/my-roadmaps.md`
- `docs/ux/features/roadmaps/roadmap-detail.md`