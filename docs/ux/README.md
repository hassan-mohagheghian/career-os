# UX Documentation

This directory contains the product and UX specifications for **Job Search Intelligence**.

## Purpose

UX docs define how the application should look and behave. They are organized in three layers:

| Directory                | Scope                                             |
| ------------------------ | ------------------------------------------------- |
| `docs/ux/design-system/` | Reusable UI primitives (Drawer, buttons, ...)     |
| `docs/ux/features/`      | Component and page specifications per feature     |
| `docs/ux/flows/`         | End-to-end user flows (steps, states, edge cases) |

## How To Read

- **Features** describe *what* a component shows (fields, sections, actions, states).
- **Flows** describe *how* a user accomplishes a goal from start to finish.
- **Design system** documents shared primitives used across all features.

Flow documents reference feature documents, and feature documents reference the design system.

## Index

```text
docs/ux/
├── README.md                  ← this index
├── design-system/
│   ├── drawer.md              Drawer (variants, placement, anatomy)
│   ├── input.md               DebouncedInput (text search / filter inputs)
│   └── README.md
├── features/
│   ├── ai/
│   │   ├── llm-configurations.md
│   │   ├── add-llm-configuration.md
│   │   ├── edit-llm-configuration.md
│   │   ├── view-llm-configuration.md
│   │   ├── enable-llm-configuration.md
│   │   ├── disable-llm-configuration.md
│   │   └── delete-llm-configuration.md
│   └── jobs/
│       ├── page.md            Jobs page (list, toolbar, infinite scroll)
│       ├── job-row.md         Job row columns and scores
│       ├── add-job.md         Add Job drawer
│       ├── edit-job.md        Edit Job drawer
│       ├── delete-job.md      Delete Job
│       ├── processing-queue.md
│       └── workflow-progress.md
└── flows/
    └── jobs/
        ├── browse-jobs.md     Browse, search, filter, sort
        ├── create-job.md      Create job (import only)
        ├── queue-job.md       Create job + immediately queue (instant workflow)
        ├── edit-job.md        Edit a job's core data
        ├── delete-job.md      Delete a job
        ├── process-job.md     Start processing
        ├── process-job-live.md
        ├── processing-queue.md
        └── ...
```

## Current Focus

The current product focus is the **Jobs** workspace:

- Browse jobs with infinite scrolling (`docs/ux/features/jobs/page.md`).
- Import jobs via the Add Job drawer (`docs/ux/features/jobs/add-job.md`).
- Edit job core data (`docs/ux/features/jobs/edit-job.md`).
- Delete a job and all its processing data (`docs/ux/features/jobs/delete-job.md`).
- Monitor AI processing through the Processing Queue (`docs/ux/features/jobs/processing-queue.md`, `docs/ux/flows/jobs/processing-queue.md`).
- Watch live workflow progress (`docs/ux/flows/jobs/process-job-live.md`).

## Design Language

- Built on **shadcn/ui** + Tailwind CSS.
- Custom density tokens `text-3xs` (6px) / `text-2xs` (8px).
- Status colors: gray (ready), blue (queued), cyan (running), green (completed), red (failed), orange (cancelled).
- Score grades: A++/A+ green, A lime, B blue, C orange, D red.
- All UI is keyboard accessible and follows WCAG AA.

For the visual design summary and wireframes see `DESIGN.md` at the repository root.
