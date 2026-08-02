# FSD Dependency Rules

## Core Rule

Higher layers may depend on lower layers. Lower layers must never depend on higher layers.

```
pages → widgets → features → entities → shared
```

## Import Rules

1. `app/` may import from all layers
2. `widgets/` may import from `features/`, `entities/`, `shared/`
3. `features/` may import from `entities/`, `shared/`
4. `entities/` may import from `shared/` only
5. `shared/` must NOT import from any other layer

## Folder Conventions

- PascalCase for components and files
- camelCase for hooks, utilities, and functions
- kebab-case for directories (optional)
- Co-locate tests with implementation (`.test.tsx`)

## What NOT to do

- ❌ Circular dependencies between features
- ❌ Importing from `pages/` inside `entities/`
- ❌ Business logic in `shared/`
- ❌ Multiple entities in a single file
- ❌ Direct `fetch()` calls in components (use entity APIs)

## Common Mistakes

- **Wrong UI component path** — UI components live in `shared/ui/`, not `components/ui/`. Feature-specific components live in `features/{name}/components/`. Stale import paths cause Vite "Could not load" build errors.
