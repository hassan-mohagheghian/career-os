# Flow: Generate a Roadmap from an Application

## Goal

From a job application in the Application Workspace, generate an AI roadmap
(goal + milestones + tasks) grounded in the job/company/candidate intelligence,
watch it generate live, then open and work through it.

## Actors & Entry

- **Actor**: signed-in user on `/jobs/{job_id}/application`.

## Steps

```mermaid
flowchart TD
    A["Application Workspace — Roadmap section (empty)"] -->|"Click ⚡ Generate roadmap"| B["POST /api/applications/{id}/roadmap/generate"]
    B -->|"202 {artifact: roadmap}"| C["SSE GenerationProgress card appears"]
    C -->|"execution.step events"| D["Worker: load_context → generate → persist"]
    D -->|"execution.completed"| E["Roadmap query invalidated; RoadmapReadyCard appears"]
    E -->|"Click View roadmap"| F["/roadmaps/{id} detail page"]
    F -->|"Add milestone / task / check off"| G["Track progress; roadmap % updates in workspace too"]
```

## Sequence (generate → SSE → complete → open)

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant W as Worker
    participant S as SSE

    U->>F: Generate roadmap
    F->>B: POST /api/applications/{id}/roadmap/generate
    B-->>F: 202 queued (artifact=roadmap)
    B->>W: dispatch ExecutionType.ROADMAP_GENERATION
    W-->>S: step / completed / failed events
    S-->>F: SSE progress (target_type=application)
    F->>B: GET /api/roadmaps/by-application/{id} (rewritted)
    B-->>F: RoadmapDetail
    F->>U: RoadmapReadyCard → View roadmap
```

## States in the Workspace section

```text
1. EMPTY        No roadmap yet + [Generate roadmap]
2. GENERATING   GenerationProgress card (spinner step) — button disabled
3. DONE         RoadmapReadyCard (title/goal/progress + View/Regenerate/Delete)
4. FAILED       GenerationProgress shows execute error; Retry re-dispatches
5. DELETED      back to EMPTY
```

## Edge Cases

| Case | Behavior |
| ---- | -------- |
| Application has no roadmap yet | Empty state; Generate enabled |
| Generation already running | Generate/Regenerate disabled until settled |
| Dispatch returns 404 (bad app id) | Error toast; button re-enabled |
| Execution fails | SSE error surfaced in the progress card; Retry |
| Regenerate while a roadmap exists | New run queued; old roadmap shown until new persists |
| Roadmap deleted from detail | Workspace section returns to empty state |

# Related Documents

- `docs/ux/features/roadmaps/roadmap-generation.md`
- `docs/ux/features/roadmaps/roadmap-detail.md`
- `docs/ux/features/applications/workspace.md`
- `docs/ai/application-intelligence.md`
- `docs/domain/overview.md` (roadmaps context)