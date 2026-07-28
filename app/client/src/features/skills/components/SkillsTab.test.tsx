import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import SkillsTab from './SkillsTab'

vi.mock('../hooks/useSkills', () => ({
  useSkills: () => ({
    skillRoadmapProgress: {},
    skillGenJobs: [],
    refreshSkillRoadmapProgress: vi.fn(),
    dashboardData: null,
    refresh: vi.fn(),
    refreshing: false,
  }),
}))

vi.mock('@/features/insights/components/SkillsIntelSection', () => ({
  default: () => <div data-testid="skills-intel-section">SkillsIntelSection</div>,
}))

describe('SkillsTab', () => {
  it('renders without crashing', () => {
    render(<SkillsTab />)
    expect(screen.getByTestId('skills-intel-section')).toBeInTheDocument()
  })

  it('renders Skills Intelligence section', () => {
    render(<SkillsTab />)
    expect(screen.getByText('SkillsIntelSection')).toBeInTheDocument()
  })
})
