# Prompt 204 - Frontend Authentication (Login, Auth Context, Route Guard)

## Objective

Add JWT-based authentication to the frontend: login/register page, AuthContext with localStorage persistence, auto-injection of Authorization header in all API calls, route guard for protected pages, and user display + logout in sidebar.

## Current State

- No auth infrastructure in the frontend whatsoever
- HTTP client (`src/shared/api/http-client.ts`) has no token injection
- No login page, no auth context, no protected routes
- Backend auth endpoints working: POST /api/auth/login, POST /api/auth/register, GET /api/auth/me

## Changes

### 1. Auth Types (`src/shared/types/auth.ts`)
- `User` interface (id, username, display_name, created_at)
- `AuthResponse` interface (token, user)

### 2. Auth Context (`src/shared/lib/auth-context.tsx`)
- `AuthProvider` wrapping app — stores token + user in localStorage
- `useAuth()` hook — exposes `user`, `token`, `isLoading`, `isAuthenticated`, `login()`, `logout()`, `setUser()`
- Token key: `js_auth_token`, User key: `js_auth_user`

### 3. HTTP Client (`src/shared/api/http-client.ts`)
- `getAuthHeaders()` reads token from localStorage and injects `Authorization: Bearer <token>`
- 401 responses auto-clear token and redirect to `/login`
- New `authApi` export with `login()`, `register()`, `me()` methods

### 4. Login Page (`app/login/page.tsx`)
- Toggle between Login / Register modes
- Form fields: username, password (+ display_name for register)
- Calls authApi, stores token via AuthContext, redirects to /jobs

### 5. Route Guard (`src/shared/lib/auth-guard.tsx`)
- `AuthGuard` component wraps the app
- Redirects unauthenticated users to /login
- Redirects authenticated users away from /login to /jobs
- Public paths: ['/login']

### 6. Providers (`src/app/providers.tsx`)
- AuthProvider wraps QueryClientProvider (outermost)
- AuthGuard wraps QueryClientProvider (inside AuthProvider)

### 7. Sidebar (`src/widgets/sidebar/index.tsx`)
- Shows user avatar (initial), display name, @username in bottom section
- Logout button (SignOut icon) in sidebar and mobile drawer
- Calls `logout()` and redirects to /login

## Files Modified

| File | Change |
|------|--------|
| `src/shared/types/auth.ts` | New — auth types |
| `src/shared/lib/auth-context.tsx` | New — AuthProvider + useAuth |
| `src/shared/lib/auth-guard.tsx` | New — route guard |
| `src/shared/api/http-client.ts` | Modified — token injection, 401 redirect, authApi |
| `app/login/page.tsx` | New — login/register page |
| `src/app/providers.tsx` | Modified — wrap with AuthProvider + AuthGuard |
| `src/widgets/sidebar/index.tsx` | Modified — user info + logout button |

## Testing

```bash
cd apps/frontend && npx tsc --noEmit   # No new TS errors
npm run lint                           # No new lint errors
```

## Constraints

- No JavaScript files — all TypeScript
- Follow existing shadcn/ui patterns
- Token stored in localStorage (not cookies)
- AuthGuard prevents rendering protected pages while loading
