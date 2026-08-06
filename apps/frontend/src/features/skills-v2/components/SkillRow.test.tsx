import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { SkillRow } from './SkillRow'
import type { SkillListItem } from '@/entities/skill/types'

function makeSkill(overrides: Partial<SkillListItem> = {}): SkillListItem {
  return {
    id: 1,
    name: 'Kubernetes',
    level: 4,
    roles: 'DevOps engineer, Platform engineer',
    path: '',
    category: 'engineering',
    confidence: 0.85,
    market_relevance: 0.9,
    evidence: null,
    tags: ['containers', 'k8s'],
    aliases: [],
    created_at: '2026-08-01T00:00:00Z',
    ...overrides,
  }
}

function renderRow(skill: SkillListItem) {
  return render(
    <SkillRow
      skill={skill}
      onViewDetails={vi.fn()}
      onEdit={vi.fn()}
      onDelete={vi.fn()}
    />
  )
}

describe('SkillRow', () => {
  it('renders name, category, level and roles', () => {
    renderRow(makeSkill())

    expect(screen.getByText('Kubernetes')).toBeInTheDocument()
    expect(screen.getByText('engineering')).toBeInTheDocument()
    expect(screen.getByText('Lv.4')).toBeInTheDocument()
    expect(screen.getByText(/DevOps engineer/)).toBeInTheDocument()
  })

  it('renders confidence and demand percentages', () => {
    renderRow(makeSkill())
    expect(screen.getByText('90%')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('renders em dashes when confidence and demand are absent', () => {
    renderRow(makeSkill({ confidence: null, market_relevance: null }))
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('shows the alias badge when aliases exist', () => {
    renderRow(makeSkill({ aliases: ['K8s'] }))
    expect(screen.getByText('1 alias')).toBeInTheDocument()
  })

  it('calls onViewDetails on row click', () => {
    const onViewDetails = vi.fn()
    render(
      <SkillRow
        skill={makeSkill()}
        onViewDetails={onViewDetails}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    screen.getByText('Kubernetes').click()
    expect(onViewDetails).toHaveBeenCalledWith(1)
  })
})
