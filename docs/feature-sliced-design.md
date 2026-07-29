# Feature-Sliced Design (FSD)

## Overview

Feature-Sliced Design is a frontend architecture methodology that structures code by business domains and layers.

## Layers

### app/ (Next.js app/)
Application bootstrap, providers, global layouts, routing, error boundaries.

### pages/ (Next.js app/ routes)
Route composition — assembles widgets and features. No business logic.

### widgets/
Large reusable UI blocks that compose features and entities.
- Sidebar, Header, Navigation
- Page-level compositions (JobsPage, CompaniesPage, etc.)
- Drawers, Modals

### features/
User actions and interactions.
- Create Job, Edit Company, Delete Skill
- Login, Logout, Upload Resume
- Each feature owns: api/, model/, ui/, lib/

### entities/
Business entities and domain models.
- Job, Company, Skill, Rule, User
- Each entity owns: types, API, hooks, components

### shared/
Reusable infrastructure with NO business logic.
- UI Kit (shadcn/ui)
- HTTP Client
- Utilities
- Types
- Hooks
