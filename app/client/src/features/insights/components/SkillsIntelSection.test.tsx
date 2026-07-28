import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import SkillsIntelSection from './SkillsIntelSection'

vi.mock('@/shared/hooks/useSocketIO', () => ({
  useSocketIO: () => ({ on: vi.fn(), off: vi.fn() }),
  watchSkills: vi.fn(),
  unwatchSkills: vi.fn(),
}))

vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children }: any) => <div>{children}</div>,
  closestCenter: vi.fn(),
  PointerSensor: vi.fn(),
  useSensor: vi.fn(),
  useSensors: vi.fn(() => ({})),
}))

vi.mock('@dnd-kit/sortable', () => ({
  SortableContext: ({ children }: any) => <div>{children}</div>,
  useSortable: () => ({ attributes: {}, listeners: {}, setNodeRef: vi.fn(), transform: null, transition: null, isDragging: false }),
  verticalListSortingStrategy: vi.fn(),
}))

vi.mock('@dnd-kit/utilities', () => ({
  CSS: { Transform: { toString: () => '' } },
}))

describe('SkillsIntelSection', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    ))
  })

  const defaultProps = {
    data: {},
    refreshing: { skills: false },
    onRefresh: vi.fn(),
    roadmapProgress: {},
    onRefreshProgress: vi.fn(),
    genJobs: [],
    status: {},
    deepLinkSkill: null,
    onClearDeepLink: vi.fn(),
  }

  it('renders Skills Intelligence header', async () => {
    render(<SkillsIntelSection {...defaultProps} />)
    expect(screen.getByText('Skills Intelligence')).toBeInTheDocument()
  })

  it('renders Refresh button', async () => {
    render(<SkillsIntelSection {...defaultProps} />)
    expect(screen.getByText('Refresh')).toBeInTheDocument()
  })

  it('renders Merge button', async () => {
    render(<SkillsIntelSection {...defaultProps} />)
    expect(screen.getByText('Merge')).toBeInTheDocument()
  })

  it('renders Add Skill button', async () => {
    render(<SkillsIntelSection {...defaultProps} />)
    expect(screen.getByText('Add Skill')).toBeInTheDocument()
  })

  it('renders category tabs', async () => {
    render(<SkillsIntelSection {...defaultProps} />)
    expect(screen.getByText('Technical')).toBeInTheDocument()
    expect(screen.getByText('Engineering')).toBeInTheDocument()
    expect(screen.getByText('Professional')).toBeInTheDocument()
    expect(screen.getByText('Domain')).toBeInTheDocument()
    expect(screen.getByText('Career')).toBeInTheDocument()
  })

  it('renders "No skills match" when empty', async () => {
    render(<SkillsIntelSection {...defaultProps} />)
    await waitFor(() => {
      expect(screen.getByText('No skills match the current filters')).toBeInTheDocument()
    })
  })

  it('renders skills when data provided', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.includes('/api/skills')) return Promise.resolve({ ok: true, json: () => Promise.resolve([{ id: 1, name: 'React', category: 'technical', source: 'user', level: 3 }]) })
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    }))
    render(<SkillsIntelSection {...defaultProps} />)
    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument()
    })
  })

  it('renders sort options', async () => {
    render(<SkillsIntelSection {...defaultProps} />)
    expect(screen.getByText('Strength')).toBeInTheDocument()
  })

  it('opens add skill form when Add Skill clicked', async () => {
    render(<SkillsIntelSection {...defaultProps} />)
    screen.getByText('Add Skill').click()
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Skill name for/)).toBeInTheDocument()
    })
  })

  it('toggles merge mode', async () => {
    render(<SkillsIntelSection {...defaultProps} />)
    screen.getByText('Merge').click()
    await waitFor(() => {
      expect(screen.getByText('Exit Merge')).toBeInTheDocument()
    })
  })

  it('renders hidden skills section', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.includes('/api/skills/hidden')) return Promise.resolve({ ok: true, json: () => Promise.resolve([{ id: 1, name: 'HiddenSkill', category: 'technical' }]) })
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    }))
    render(<SkillsIntelSection {...defaultProps} />)
    await waitFor(() => {
      expect(screen.getByText('Hidden Skills')).toBeInTheDocument()
    })
  })
})
