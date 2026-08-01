# Frontend Architecture

## Overview

The frontend is a Next.js application using the App Router and Feature-Sliced Design (FSD) methodology.

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **Server State**: TanStack Query (React Query v5)
- **Real-time**: Socket.IO (singleton client)
- **Icons**: Phosphor Icons

## Architecture Diagram

```
app/                    ← Next.js App Router (FSD app layer)
├── layout.tsx          ← Root layout, providers
├── page.tsx            ← Redirect to /jobs
├── jobs/page.tsx       ← Jobs route
├── companies/page.tsx  ← Companies route
├── skills/page.tsx     ← Skills route
├── resume/page.tsx     ← Resume route
└── rules/page.tsx      ← Rules route

src/
├── app/                ← FSD app layer (providers, bootstrap)
│   └── providers.tsx   ← TanStack Query + Theme + Tooltip providers
├── entities/           ← Business entities (Job, Company, Skill, etc.)
│   ├── job/            ← Job types, API, hooks
│   ├── company/        ← Company types, API, hooks
│   ├── skill/          ← Skill types, API
│   └── rule/           ← Rule types, API
├── features/           ← User actions & interactions
│   └── ...             ← (migrated from legacy features/)
├── widgets/            ← Composite UI blocks
│   ├── sidebar/        ← Navigation sidebar
│   ├── header/         ← Top header bar
│   ├── main-layout/    ← Main layout wrapper
│   ├── jobs-page/      ← Jobs page composition
│   └── ...             ← Other page widgets
└── shared/             ← Reusable infrastructure
    ├── api/            ← HTTP client, API helpers
    ├── ui/             ← shadcn/ui primitives
    ├── lib/            ← Utilities (cn, formatTimeAgo, etc.)
    ├── hooks/          ← Shared hooks (WebSocket, workflow)
    ├── config/         ← Constants, configuration
    └── types/          ← Shared TypeScript types
```

## Layer Dependencies

```
pages (app/ routes)
    ↓
widgets
    ↓
features
    ↓
entities
    ↓
shared
```

Lower layers never import from higher layers.

## Routing

- Next.js App Router with file-based routing
- All pages are Client Components (dynamic import with ssr: false)
- No legacy hash-based routing
