import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import SkillsTab from './SkillsTab'

vi.mock('../hooks/useSkills', () => ({
  useSkills: () => ({
    skills: [],
    skillRoadmapProgress: {},
    skillGenJobs: [],
    fetchSkills: vi.fn(),
    dashboardData: null,
    refresh: vi.fn(),
    refreshing: false,
  }),
}))

vi.mock('./SkillDetailDrawer', () => ({
  default: () => null,
}))

describe('SkillsTab', () => {
  it('renders without crashing', () => {
    render(<SkillsTab />)
  })
})
