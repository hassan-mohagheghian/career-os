import { describe, it, expect } from 'vitest'
import { SOURCE_CONFIG, PROVIDER_LABELS } from './sourceConfig'

describe('SOURCE_CONFIG', () => {
  it('has config for job-processing', () => {
    expect(SOURCE_CONFIG['job-processing']).toBeDefined()
    expect(SOURCE_CONFIG['job-processing'].label).toBe('Job')
    expect(SOURCE_CONFIG['job-processing'].color).toContain('blue')
  })

  it('has config for company-processing', () => {
    expect(SOURCE_CONFIG['company-processing']).toBeDefined()
    expect(SOURCE_CONFIG['company-processing'].label).toBe('Company')
  })

  it('has config for generation', () => {
    expect(SOURCE_CONFIG['generation']).toBeDefined()
    expect(SOURCE_CONFIG['generation'].label).toBe('Generate')
  })

  it('has config for insights', () => {
    expect(SOURCE_CONFIG['insights']).toBeDefined()
    expect(SOURCE_CONFIG['insights'].label).toBe('Intel')
  })

  it('has config for roadmap', () => {
    expect(SOURCE_CONFIG['roadmap']).toBeDefined()
    expect(SOURCE_CONFIG['roadmap'].label).toBe('Roadmap')
  })

  it('each config has icon, color, and label', () => {
    for (const [key, config] of Object.entries(SOURCE_CONFIG)) {
      expect(config.icon, `${key} missing icon`).toBeDefined()
      expect(config.color, `${key} missing color`).toBeTruthy()
      expect(config.label, `${key} missing label`).toBeTruthy()
    }
  })
})

describe('PROVIDER_LABELS', () => {
  it('maps mimo to MiMo', () => {
    expect(PROVIDER_LABELS['mimo']).toBe('MiMo')
  })

  it('maps agent to Agent', () => {
    expect(PROVIDER_LABELS['agent']).toBe('Agent')
  })

  it('maps claude to Claude', () => {
    expect(PROVIDER_LABELS['claude']).toBe('Claude')
  })

  it('maps openai to OpenAI', () => {
    expect(PROVIDER_LABELS['openai']).toBe('OpenAI')
  })

  it('maps opencode to opencode', () => {
    expect(PROVIDER_LABELS['opencode']).toBe('opencode')
  })
})
