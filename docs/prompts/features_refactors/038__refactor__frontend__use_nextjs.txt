# Sprint 16 — Migrate Frontend to Next.js App Router using Feature-Sliced Design (FSD)

## ROLE

You are a Principal Frontend Architect, Next.js Expert, React Expert, TypeScript Expert, TanStack Query Expert, and Software Architect.

Your task is to redesign the entire frontend architecture.

The current frontend is implemented as a traditional Single Page Application.

The target architecture is a modern Next.js application using:

- Next.js App Router
- Feature-Sliced Design (FSD)
- TypeScript
- TanStack Query

Business functionality must remain unchanged.

The architecture should become scalable, maintainable, and aligned with Domain-Driven Design principles used by the backend.

--------------------------------------------------
OBJECTIVES
--------------------------------------------------

Completely migrate the frontend from SPA to Next.js App Router.

Adopt Feature-Sliced Design (FSD) instead of a simple Feature-Based architecture.

Improve scalability, modularity, maintainability, and developer experience.

--------------------------------------------------
TARGET ARCHITECTURE
--------------------------------------------------

Use Feature-Sliced Design.

The project should be organized into layers similar to:

app/

processes/ (optional, only if truly needed)

pages/

widgets/

features/

entities/

shared/

Each layer must have a clearly defined responsibility.

--------------------------------------------------
LAYER RESPONSIBILITIES
--------------------------------------------------

app/

Application bootstrap

Providers

Global Layouts

Theme

Routing

Authentication bootstrap

Error boundaries

Global configuration

--------------------------------------------------

pages/

Route composition.

A page should assemble widgets and features.

Avoid business logic here.

Examples:

jobs

companies

skills

rules

dashboard

settings

--------------------------------------------------

widgets/

Large reusable UI blocks.

Examples:

Job Table

Company Dashboard

Sidebar

Header

Navigation

Status Panel

Statistics Cards

Widgets compose features and entities.

--------------------------------------------------

features/

User actions.

Examples:

Create Job

Edit Company

Delete Skill

Retry Processing

Login

Logout

Upload Resume

Each feature owns:

api/

model/

ui/

lib/

config/

--------------------------------------------------

entities/

Business entities.

Examples:

Job

Company

Skill

Rule

User

Entity layer owns:

Types

Business models

Entity API

Entity Hooks

Entity Components

Entity utilities

--------------------------------------------------

shared/

Reusable infrastructure.

Examples:

UI Kit

HTTP Client

TanStack Query Client

WebSocket Client

Utilities

Constants

Types

Helpers

Icons

Theme

Validation

Date utilities

Common Hooks

No business logic belongs here.

--------------------------------------------------
NEXT.JS

Use:

App Router

Nested Layouts

Loading UI

Error UI

Server Components

Streaming

Suspense

Metadata API

Not Found pages

Route Groups when appropriate.

--------------------------------------------------
SERVER COMPONENTS

Prefer Server Components whenever possible.

Use Client Components only when required.

Examples:

Forms

WebSockets

Interactive Tables

Local UI State

Animations

Avoid unnecessary "use client".

--------------------------------------------------
TANSTACK QUERY

Use TanStack Query as the single server-state solution.

Every feature should expose:

Queries

Mutations

Optimistic Updates (where appropriate)

Infinite Queries (when needed)

Avoid manual loading and caching logic.

--------------------------------------------------
WEBSOCKET

Create one shared WebSocket infrastructure.

Entity- or feature-level subscriptions should consume it.

Examples:

Job Status

Company Status

Notifications

Progress

Do not duplicate socket implementations.

--------------------------------------------------
API ORGANIZATION

Every entity owns its API.

Example:

entities/job/api/

entities/company/api/

Features consume entity APIs.

Avoid duplicated HTTP implementations.

--------------------------------------------------
FORMS

Use a consistent form architecture.

Validation schemas should live close to the owning feature.

--------------------------------------------------
STATE MANAGEMENT

Do NOT introduce Redux or another global state library unless strictly necessary.

Prefer:

TanStack Query

React Context

Server Components

Local Component State

--------------------------------------------------
CODE ORGANIZATION

Respect FSD dependency rules.

Higher layers may depend on lower layers.

Lower layers must never depend on higher layers.

Example:

pages

↓

widgets

↓

features

↓

entities

↓

shared

Never reverse dependencies.

--------------------------------------------------
PERFORMANCE

Optimize:

Streaming

Suspense

Dynamic Imports

Image Optimization

Code Splitting

Bundle Size

Server Rendering

Avoid unnecessary client-side rendering.

--------------------------------------------------
TESTING

Refactor all frontend tests.

Add tests for:

Entities

Features

Widgets

Pages

Queries

Mutations

Routing

--------------------------------------------------
DOCUMENTATION

Create:

docs/frontend-architecture.md

docs/feature-sliced-design.md

docs/nextjs-app-router.md

docs/tanstack-query.md

docs/websocket.md

docs/fsd-rules.md

docs/adr/016-nextjs-fsd-migration.md

Document:

Layer responsibilities

Dependency rules

Folder conventions

Naming conventions

Import rules

--------------------------------------------------
CLEANUP

Remove:

Legacy SPA routing

Legacy API layer

Duplicated hooks

Duplicated components

Unused utilities

Dead code

Legacy state management

--------------------------------------------------
ACCEPTANCE CRITERIA

✔ Frontend runs entirely on Next.js App Router.

✔ Feature-Sliced Design is fully implemented.

✔ Layer dependency rules are respected.

✔ Entities, Features, Widgets, Pages, and Shared are clearly separated.

✔ TanStack Query manages all server state.

✔ WebSocket integration remains fully functional.

✔ Legacy SPA infrastructure is removed.

✔ Existing functionality is preserved.

✔ The architecture is scalable, maintainable, and aligned with backend DDD principles.

✔ The project is ready for long-term growth with minimal architectural changes.
