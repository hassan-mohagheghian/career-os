import { describe, it, expect } from 'vitest'
import { resolveSkillCategory, filterByCategory } from '@/lib/skills'

const techStackSkills = [
  { name: 'Python', category: 'technical', level: 4 },
  { name: 'PostgreSQL', category: 'technical', level: 3 },
  { name: 'System Design', category: 'engineering', level: 2 },
]

const aiReport = {
  strengths: [
    { skill: 'Python', category: 'technical', confidence: 0.9 },
    { skill: 'Leadership', category: 'professional', confidence: 0.7 },
  ],
  gaps: [
    { skill: 'Kubernetes', category: 'engineering', confidence: 0.8 },
    { skill: 'Stakeholder Management', category: 'professional', confidence: 0.6 },
  ],
  learningRecommendations: [
    { skill: 'AWS Solutions Architect', category: 'career', roi: 8 },
    { skill: 'Fintech Domain Knowledge', category: 'domain', roi: 6 },
  ],
}

describe('resolveSkillCategory', () => {
  it('returns category from tech_stack when skill exists there', () => {
    expect(resolveSkillCategory('Python', techStackSkills, aiReport)).toBe('technical')
  })

  it('returns category from tech_stack even if AI report has different category', () => {
    // tech_stack is authoritative when present
    expect(resolveSkillCategory('System Design', techStackSkills, aiReport)).toBe('engineering')
  })

  it('falls back to strengths category when skill is not in tech_stack', () => {
    expect(resolveSkillCategory('Leadership', techStackSkills, aiReport)).toBe('professional')
  })

  it('falls back to gaps category when skill is not in tech_stack', () => {
    expect(resolveSkillCategory('Kubernetes', techStackSkills, aiReport)).toBe('engineering')
  })

  it('falls back to recommendations category when skill is not in tech_stack', () => {
    expect(resolveSkillCategory('AWS Solutions Architect', techStackSkills, aiReport)).toBe('career')
  })

  it('returns undefined for skill not found anywhere', () => {
    expect(resolveSkillCategory('UnknownSkill', techStackSkills, aiReport)).toBeUndefined()
  })

  it('returns undefined when tech_stack and aiReport are empty', () => {
    expect(resolveSkillCategory('Python', [], {})).toBeUndefined()
  })
})

describe('filterByCategory', () => {
  it('filters strengths by resolved category', () => {
    const result = filterByCategory(
      aiReport.strengths, 'professional', techStackSkills, aiReport
    )
    expect(result).toHaveLength(1)
    expect(result[0].skill).toBe('Leadership')
  })

  it('filters gaps by resolved category', () => {
    const result = filterByCategory(
      aiReport.gaps, 'engineering', techStackSkills, aiReport
    )
    expect(result).toHaveLength(1)
    expect(result[0].skill).toBe('Kubernetes')
  })

  it('filters recommendations by resolved category', () => {
    const result = filterByCategory(
      aiReport.learningRecommendations, 'career', techStackSkills, aiReport
    )
    expect(result).toHaveLength(1)
    expect(result[0].skill).toBe('AWS Solutions Architect')
  })

  it('returns empty when no items match category', () => {
    const result = filterByCategory(
      aiReport.strengths, 'nonexistent', techStackSkills, aiReport
    )
    expect(result).toHaveLength(0)
  })
})
