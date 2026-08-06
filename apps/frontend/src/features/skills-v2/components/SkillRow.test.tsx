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
    source_type: 'user_input',
    mention_count: 0,
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

  it('shows an AI origin badge for ai_generated skills', () => {
    renderRow(makeSkill({ source_type: 'ai_generated' }))
    expect(screen.getByText('AI')).toBeInTheDocument()
  })

  it('shows a Manual origin badge for user_input skills', () => {
    renderRow(makeSkill({ source_type: 'user_input' }))
    expect(screen.getByText('Manual')).toBeInTheDocument()
  })

  it('shows the mention count', () => {
    renderRow(makeSkill({ mention_count: 7 }))
    expect(screen.getByText('7')).toBeInTheDocument()
  })

  it('shows zero mentions', () => {
    renderRow(makeSkill({ mention_count: 0 }))
    expect(screen.getByText('0')).toBeInTheDocument()
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
