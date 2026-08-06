import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SkillsPage } from './SkillsPage'
import type { SkillListItem } from '@/entities/skill/types'

vi.mock('@/entities/skill/hooks', () => ({
  useCreateSkill: () => ({
    createSkill: vi.fn().mockResolvedValue(true),
    submitting: false,
    error: null,
    clearError: vi.fn(),
  }),
}))

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

function makeSkill(id: number, name: string): SkillListItem {
  return {
    id,
    name,
    level: 3,
    roles: '',
    path: '',
    category: 'technical',
    confidence: 0.8,
    market_relevance: 0.9,
    evidence: null,
    tags: [],
    aliases: [],
    source_type: 'user_input',
    mention_count: 0,
    created_at: '2026-08-01T00:00:00Z',
  }
}

function baseProps(overrides: Partial<Parameters<typeof SkillsPage>[0]> = {}): Parameters<typeof SkillsPage>[0] {
  return {
    items: [],
    total: 0,
    loadedCount: 0,
    isLoading: false,
    isFetchingNextPage: false,
    hasNextPage: false,
    onFetchNextPage: vi.fn(),
    isError: false,
    error: null,
    onRefetch: vi.fn(),
    query: '',
    onQueryChange: vi.fn(),
    sort: 'mention_count',
    onSortChange: vi.fn(),
    order: 'desc',
    filterCategory: '',
    onFilterCategoryChange: vi.fn(),
    activeFilterCount: 0,
    onClearFilters: vi.fn(),
    onViewDetails: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    addSkillDrawerOpen: false,
    onAddSkillDrawerOpenChange: vi.fn(),
    detailSkillId: null,
    onDetailSkillIdChange: vi.fn(),
    editSkillId: null,
    onEditSkillIdChange: vi.fn(),
    ...overrides,
  }
}

function renderPage(props: Parameters<typeof SkillsPage>[0]) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <SkillsPage {...props} />
    </QueryClientProvider>
  )
}

describe('SkillsPage', () => {
  it('renders the header with total count', () => {
    renderPage(baseProps({ total: 12 }))
    expect(screen.getByText(/Skills \(12\)/)).toBeInTheDocument()
  })

  it('shows empty state when there are no skills', () => {
    renderPage(baseProps())
    expect(screen.getByText(/No skills yet/)).toBeInTheDocument()
  })

  it('renders the toolbar and rows are rendered via the virtualized table', () => {
    renderPage(baseProps({
      items: [makeSkill(1, 'Kubernetes'), makeSkill(2, 'Python')],
      total: 2,
      loadedCount: 2,
    }))
    expect(screen.getByText(/Skills \(2\)/)).toBeInTheDocument()
  })

  it('shows the error state with a retry button', () => {
    renderPage(baseProps({
      isError: true,
      error: new Error('boom'),
    }))
    expect(screen.getByText('Unable to load skills')).toBeInTheDocument()
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })
})
