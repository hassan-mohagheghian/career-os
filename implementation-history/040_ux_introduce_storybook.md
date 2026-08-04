You are working on an existing Next.js + TypeScript project using Feature-Sliced Design.

Goal:
Add a professional Storybook + Design System workflow without changing the existing FSD architecture.

Important:
Do not create a separate prototype app.
Do not implement new Jobs UI.
Do not move existing features.

Tasks:

1. Install and configure Storybook for the existing Next.js application.

Requirements:
- React + TypeScript support
- Next.js compatibility
- Add scripts:
  - storybook
  - build-storybook

2. Respect the current FSD layers:

src/
├── app
├── widgets
├── features
├── entities
└── shared


3. Define UI ownership rules:

shared/ui:
- shadcn/ui primitives only
- Button
- Card
- Badge
- Dialog
- Input
- Table

entities/*/ui:
- Domain components
- Example:
  entities/job/ui/job-card.tsx

features/*/ui:
- User actions and workflows
- Example:
  features/import-job/ui/import-job-dialog.tsx

widgets/*:
- Page-level compositions


4. Add Storybook examples:

Create stories for existing shared UI components.

Example:

shared/ui/button.stories.tsx
shared/ui/card.stories.tsx
shared/ui/badge.stories.tsx


5. Add documentation:

docs/ux/design-system/

Include:
- FSD UI organization rules
- Storybook usage
- shadcn/ui conventions
- Component ownership rules


6. Add configuration only.
Do not create business components or new product screens.

7. Verify:

npm run storybook
npm run build-storybook

Expected result:

Figma
 ↓
FSD Components
 ↓
Storybook
 ↓
Next.js Application
 ↓
FastAPI APIs
