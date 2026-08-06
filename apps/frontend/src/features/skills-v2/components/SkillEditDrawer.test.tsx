import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SkillEditDrawer } from './SkillEditDrawer'
import { skillApi } from '@/entities/skill/api'

vi.mock('@/entities/skill/api', () => ({
  skillApi: {
    get: vi.fn(),
    update: vi.fn(),
  },
}))

function renderDrawer(skillId: number | null, onOpenChange: (id: number | null) => void = vi.fn()) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <SkillEditDrawer skillId={skillId} onOpenChange={onOpenChange} />
    </QueryClientProvider>
  )
}

describe('SkillEditDrawer', () => {
  beforeEach(() => {
    vi.mocked(skillApi.get).mockResolvedValue({
      id: 1,
      name: 'Kubernetes',
      level: 4,
      roles: 'DevOps',
      path: '',
      category: 'engineering',
      confidence: 0.85,
      market_relevance: 0.9,
      evidence: null,
      tags: ['containers', 'k8s'],
      aliases: [],
      created_at: '2026-08-01T00:00:00Z',
    })
    vi.mocked(skillApi.update).mockResolvedValue({} as never)
  })

  it('prefills the form from the loaded skill', async () => {
    renderDrawer(1)
    await waitFor(() => {
      expect(screen.getByDisplayValue('Kubernetes')).toBeInTheDocument()
    })
    expect(screen.getByDisplayValue('DevOps')).toBeInTheDocument()
    expect(screen.getByDisplayValue('containers, k8s')).toBeInTheDocument()
  })

  it('saves the updated skill via PUT and closes', async () => {
    const onOpenChange = vi.fn()
    renderDrawer(1, onOpenChange)
    await waitFor(() => {
      expect(screen.getByDisplayValue('Kubernetes')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByDisplayValue('Kubernetes'), {
      target: { value: 'Kubernetes v2' },
    })
    fireEvent.click(screen.getByText('Save'))

    await waitFor(() => {
      expect(skillApi.update).toHaveBeenCalledWith(
        1,
        expect.objectContaining({ name: 'Kubernetes v2' })
      )
    })
    expect(onOpenChange).toHaveBeenCalledWith(null)
  })
})
