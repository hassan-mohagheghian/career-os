import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MergeCityDialog } from './MergeCityDialog'
import { cityApi } from '@/entities/city/api'

vi.mock('@/entities/city/api', () => ({
  cityApi: {
    listInfinite: vi.fn(),
  },
}))

function renderDialog(open: boolean, sources: { id: string; name: string }[] = [{ id: '1', name: 'Munich, Germany' }]) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MergeCityDialog
        sources={sources}
        open={open}
        onOpenChange={vi.fn()}
        onMerge={vi.fn()}
        pending={false}
      />
    </QueryClientProvider>
  )
}

describe('MergeCityDialog', () => {
  it('lists candidate cities and excludes all source cities', async () => {
    vi.mocked(cityApi.listInfinite).mockResolvedValue({
      items: [
        { id: '1', city: 'Munich', country: 'Germany', aliases: [], job_count: 0, original_text: null, address: null, created_at: null, updated_at: null },
        { id: '2', city: 'München', country: 'Germany', aliases: [], job_count: 3, original_text: null, address: null, created_at: null, updated_at: null },
      ],
      next_cursor: null,
      has_more: false,
      total_items: 2,
    } as never)

    renderDialog(true)

    await waitFor(() => {
      expect(screen.getByText('München, Germany')).toBeInTheDocument()
    })
    const munichButtons = screen.getAllByRole('button').filter((b) => b.textContent?.includes('Munich, Germany'))
    expect(munichButtons).toHaveLength(0)
    expect(screen.getByText('3 jobs')).toBeInTheDocument()
  })

  it('excludes every source when merging multiple cities', async () => {
    vi.mocked(cityApi.listInfinite).mockResolvedValue({
      items: [
        { id: '1', city: 'Munich', country: 'Germany', aliases: [], job_count: 0, original_text: null, address: null, created_at: null, updated_at: null },
        { id: '2', city: 'Muenchen', country: 'Germany', aliases: [], job_count: 0, original_text: null, address: null, created_at: null, updated_at: null },
        { id: '3', city: 'München', country: 'Germany', aliases: [], job_count: 3, original_text: null, address: null, created_at: null, updated_at: null },
      ],
      next_cursor: null,
      has_more: false,
      total_items: 3,
    } as never)

    renderDialog(true, [
      { id: '1', name: 'Munich, Germany' },
      { id: '2', name: 'Muenchen, Germany' },
    ])

    await waitFor(() => {
      expect(screen.getByText('München, Germany')).toBeInTheDocument()
    })
    const excluded = screen.getAllByRole('button').filter(
      (b) => b.textContent?.includes('Munich, Germany') || b.textContent?.includes('Muenchen, Germany')
    )
    expect(excluded).toHaveLength(0)
    expect(screen.getByText(/Merge 2 into selected/)).toBeInTheDocument()
  })

  it('calls onMerge with the selected target', async () => {
    const onMerge = vi.fn()
    vi.mocked(cityApi.listInfinite).mockResolvedValue({
      items: [
        { id: '2', city: 'München', country: 'Germany', aliases: [], job_count: 0, original_text: null, address: null, created_at: null, updated_at: null },
      ],
      next_cursor: null,
      has_more: false,
      total_items: 1,
    } as never)

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <MergeCityDialog
          sources={[{ id: '1', name: 'Munich, Germany' }]}
          open={true}
          onOpenChange={vi.fn()}
          onMerge={onMerge}
          pending={false}
        />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('München, Germany')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('München, Germany'))
    fireEvent.click(screen.getByText(/Merge into selected/))

    await waitFor(() => {
      expect(onMerge).toHaveBeenCalledWith('2')
    })
  })
})