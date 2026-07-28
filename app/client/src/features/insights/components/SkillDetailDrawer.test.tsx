import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import SkillDetailDrawer from './SkillDetailDrawer'

vi.mock('@/shared/hooks/useSocketIO', () => ({
  useSocketIO: () => ({ on: vi.fn(), off: vi.fn() }),
  watchSkills: vi.fn(),
  unwatchSkills: vi.fn(),
}))

vi.mock('@/shared/hooks', () => ({
  useLocalHistory: () => ({ items: [], singleRunning: null }),
}))

describe('SkillDetailDrawer', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    ))
  })

  it('returns null when skillName is null', () => {
    const { container } = render(
      <SkillDetailDrawer skillName={null} open={false} onOpenChange={vi.fn()} techStackSkills={[]} roadmapProgress={{}} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('renders skill name when open', async () => {
    render(
      <SkillDetailDrawer skillName="React" open={true} onOpenChange={vi.fn()} techStackSkills={[]} roadmapProgress={{}} />
    )
    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument()
    })
  })

  it('renders tabs when open', async () => {
    render(
      <SkillDetailDrawer skillName="React" open={true} onOpenChange={vi.fn()} techStackSkills={[]} roadmapProgress={{}} />
    )
    await waitFor(() => {
      expect(screen.getByText('Details')).toBeInTheDocument()
    })
    expect(screen.getByText('Roadmap')).toBeInTheDocument()
  })

  it('renders Hide Skill button', async () => {
    render(
      <SkillDetailDrawer skillName="React" open={true} onOpenChange={vi.fn()} techStackSkills={[]} roadmapProgress={{}} />
    )
    await waitFor(() => {
      expect(screen.getByText('Hide Skill')).toBeInTheDocument()
    })
  })

  it('renders proficiency levels', async () => {
    render(
      <SkillDetailDrawer skillName="React" open={true} onOpenChange={vi.fn()} techStackSkills={[]} roadmapProgress={{}} />
    )
    await waitFor(() => {
      expect(screen.getByText('Proficiency Level')).toBeInTheDocument()
    })
  })

  it('renders market demand when skill has market_relevance', async () => {
    render(
      <SkillDetailDrawer skillName="React" open={true} onOpenChange={vi.fn()} techStackSkills={[{ name: 'React', market_relevance: 85 }]} roadmapProgress={{}} />
    )
    await waitFor(() => {
      expect(screen.getByText('Market Demand')).toBeInTheDocument()
    })
  })

  it('renders aliases when skill has them', async () => {
    render(
      <SkillDetailDrawer skillName="React" open={true} onOpenChange={vi.fn()} techStackSkills={[{ name: 'React', aliases: ['ReactJS', 'React.js'] }]} roadmapProgress={{}} />
    )
    await waitFor(() => {
      expect(screen.getByText('Merged Skills')).toBeInTheDocument()
    })
  })

  it('renders tags section', async () => {
    render(
      <SkillDetailDrawer skillName="React" open={true} onOpenChange={vi.fn()} techStackSkills={[]} roadmapProgress={{}} />
    )
    await waitFor(() => {
      expect(screen.getByText('Tags')).toBeInTheDocument()
    })
  })

  it('renders roadmap tab and no roadmap message', async () => {
    const user = userEvent.setup()
    render(
      <SkillDetailDrawer skillName="React" open={true} onOpenChange={vi.fn()} techStackSkills={[]} roadmapProgress={{}} />
    )
    await waitFor(() => {
      expect(screen.getByText('Roadmap')).toBeInTheDocument()
    })
    await user.click(screen.getByRole('tab', { name: /Roadmap/ }))
    await waitFor(() => {
      expect(screen.getByText(/No roadmap yet/)).toBeInTheDocument()
    })
  })
})
