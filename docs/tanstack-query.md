# TanStack Query (React Query v5)

## Purpose

Single server-state management solution. Replaces all manual `fetch()` calls and `useState` for server data.

## Query Client Configuration

- `staleTime`: 30 seconds
- `refetchOnWindowFocus`: false
- `retry`: 1 attempt

## Entity Queries

Each entity exposes typed hooks:
- `useJobsQuery(params)` — paginated job list
- `useJobQuery(num)` — single job
- `useCompaniesQuery()` — company list
- `useCompanyQuery(id)` — single company

## Mutations

Each write operation uses `useMutation` with automatic query invalidation:
- `useDeleteJobMutation()` → invalidates `['jobs']`
- `useUpdateJobMutation()` → invalidates `['jobs']`
- `useRequeueJobMutation()` → invalidates `['jobs']`

## Real-time Updates

Socket.IO events still handle real-time updates for in-progress operations. TanStack Query handles initial data loading and refetching after mutations.
