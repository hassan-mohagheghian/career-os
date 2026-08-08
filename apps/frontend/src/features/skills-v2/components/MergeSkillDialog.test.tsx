import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MergeSkillDialog } from './MergeSkillDialog'
import { skillApi } from '@/entities/skill/api'

vi.mock('@/entities/skill/api', () => ({
  skillApi: {
    listInfinite: vi.fn(),
  },
}))

function renderDialog(open: boolean, sources: { id: number; name: string }[] = [{ id: 1, name: 'ReactJS' }]) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MergeSkillDialog
        sources={sources}
        open={open}
        onOpenChange={vi.fn()}
        onMerge={vi.fn()}
        pending={false}
      />
    </QueryClientProvider>
  )
}

describe('MergeSkillDialog', () => {
  it('lists candidate skills and excludes all source skills', async () => {
    vi.mocked(skillApi.listInfinite).mockResolvedValue({
      items: [
        { id: 1, name: 'ReactJS', mention_count: 0 },
        { id: 2, name: 'React', mention_count: 3 },
      ],
      next_cursor: null,
      has_more: false,
      total_items: 2,
    } as never)

    renderDialog(true)

    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument()
    })
    const candidateRows = screen.getAllByRole('button').filter((b) => b.textContent?.includes('React'))
    expect(candidateRows).toHaveLength(1)
    expect(screen.getByText('3 mentions')).toBeInTheDocument()
  })

  it('excludes every source when merging multiple skills', async () => {
    vi.mocked(skillApi.listInfinite).mockResolvedValue({
      items: [
        { id: 1, name: 'ReactJS', mention_count: 0 },
        { id: 2, name: 'React Native', mention_count: 0 },
        { id: 3, name: 'React', mention_count: 3 },
      ],
      next_cursor: null,
      has_more: false,
      total_items: 3,
    } as never)

    renderDialog(true, [
      { id: 1, name: 'ReactJS' },
      { id: 2, name: 'React Native' },
    ])

    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument()
    })
    const candidateRows = screen.getAllByRole('button').filter((b) => b.textContent?.includes('React'))
    expect(candidateRows).toHaveLength(1)
    expect(screen.getByText(/Merge 2 into selected/)).toBeInTheDocument()
  })

  it('calls onMerge with the selected target', async () => {
    const onMerge = vi.fn()
    vi.mocked(skillApi.listInfinite).mockResolvedValue({
      items: [{ id: 2, name: 'React', mention_count: 0 }],
      next_cursor: null,
      has_more: false,
      total_items: 1,
    } as never)

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <MergeSkillDialog
          sources={[{ id: 1, name: 'ReactJS' }]}
          open={true}
          onOpenChange={vi.fn()}
          onMerge={onMerge}
          pending={false}
        />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('React'))
    fireEvent.click(screen.getByText(/Merge into selected/))

    await waitFor(() => {
      expect(onMerge).toHaveBeenCalledWith(2)
    })
  })
})
