import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { SkillDetailDrawer } from './SkillDetailDrawer'
import type { SkillListItem } from '@/entities/skill/types'

function makeSkill(overrides: Partial<SkillListItem> = {}): SkillListItem {
  return {
    id: 1,
    name: 'Kubernetes',
    level: 4,
    roles: 'DevOps engineer',
    path: '',
    category: 'engineering',
    categories: ['engineering', 'infrastructure'],
    confidence: 0.85,
    market_relevance: 0.9,
    evidence: null,
    tags: [],
    aliases: [],
    source_type: 'user_input',
    mention_count: 0,
    pinned: false,
    created_at: '2026-08-01T00:00:00Z',
    ...overrides,
  }
}

function renderDrawer(skill: SkillListItem) {
  return render(
    <SkillDetailDrawer
      skillId={skill.id}
      skill={skill}
      onOpenChange={vi.fn()}
      onEdit={vi.fn()}
      onDelete={vi.fn()}
    />
  )
}

describe('SkillDetailDrawer', () => {
  it('shows a dedicated Categories section with every category badge', () => {
    renderDrawer(makeSkill())

    expect(screen.getByText('Categories')).toBeInTheDocument()
    expect(screen.getByText('engineering')).toBeInTheDocument()
    expect(screen.getByText('infrastructure')).toBeInTheDocument()
  })

  it('hides the Categories section when the skill has no categories', () => {
    renderDrawer(makeSkill({ category: '', categories: [] }))
    expect(screen.queryByText('Categories')).not.toBeInTheDocument()
  })
})
