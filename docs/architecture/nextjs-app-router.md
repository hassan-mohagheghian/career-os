# Next.js App Router

## Conventions

- File-based routing under `app/` directory
- `page.tsx` — route UI
- `layout.tsx` — shared layout
- `loading.tsx` — loading UI (Suspense)
- `error.tsx` — error UI (Error Boundary)
- `not-found.tsx` — 404 page

## Client Components

All page-level components use `'use client'` with dynamic imports (`ssr: false`) because they depend on browser APIs (Socket.IO, localStorage, etc.).

## Static Generation

Pages are statically generated at build time. Client-side data fetching happens after hydration via TanStack Query.

## Rewrites

API and WebSocket requests are proxied to the backend via Next.js rewrites:
- `/api/*` → `http://localhost:5000/api/*`
- `/socket.io/*` → `http://localhost:5000/socket.io/*`
