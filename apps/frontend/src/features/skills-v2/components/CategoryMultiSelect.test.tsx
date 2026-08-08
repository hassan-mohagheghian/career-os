import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { CategoryMultiSelect } from './CategoryMultiSelect'

function renderSelect(props: Record<string, unknown> = {}) {
  const base = {
    value: [] as string[],
    onChange: vi.fn(),
    options: ['technical', 'engineering', 'professional'],
  }
  const onChange = (base.onChange as ReturnType<typeof vi.fn>)
  const result = render(<CategoryMultiSelect {...base} {...props} />)
  return { ...result, onChange }
}

describe('CategoryMultiSelect', () => {
  it('renders the placeholder when nothing is selected', () => {
    renderSelect()
    expect(screen.getByRole('button', { name: 'Filter by category' })).toBeInTheDocument()
    expect(screen.getByText('Category')).toBeInTheDocument()
  })

  it('toggles a category on click', async () => {
    const { onChange } = renderSelect()
    fireEvent.click(screen.getByLabelText('Filter by category'))
    fireEvent.click(screen.getByText('technical'))
    expect(onChange).toHaveBeenCalledWith(['technical'])
  })

  it('removes a selected category on second click', () => {
    const onChange = vi.fn()
    renderSelect({ value: ['technical', 'engineering'], onChange })
    fireEvent.click(screen.getByLabelText('Filter by category'))
    const popoverEngineering = screen.getAllByText('engineering')[1]
    fireEvent.click(popoverEngineering)
    expect(onChange).toHaveBeenCalledWith(['technical'])
  })

  it('shows selected badges in the trigger', () => {
    renderSelect({ value: ['technical', 'engineering'] })
    expect(screen.getByText('technical')).toBeInTheDocument()
    expect(screen.getByText('engineering')).toBeInTheDocument()
  })

  it('shows a +N indicator when more than three are selected', () => {
    renderSelect({ value: ['a', 'b', 'c', 'd'] })
    expect(screen.getByText('+1')).toBeInTheDocument()
  })

  it('clears the selection via the Clear button', () => {
    const onChange = vi.fn()
    renderSelect({ value: ['technical'], onChange })
    fireEvent.click(screen.getByLabelText('Filter by category'))
    fireEvent.click(screen.getByText('Clear'))
    expect(onChange).toHaveBeenCalledWith([])
  })

  it('creates a new category inline and selects it', async () => {
    const onChange = vi.fn()
    const onCreate = vi.fn().mockResolvedValue({ name: 'data' })
    renderSelect({ onChange, onCreate })

    fireEvent.click(screen.getByLabelText('Filter by category'))
    fireEvent.change(screen.getByPlaceholderText('Add category...'), { target: { value: 'data' } })
    fireEvent.click(screen.getByLabelText('Add category'))

    await waitFor(() => {
      expect(onCreate).toHaveBeenCalledWith('data')
      expect(onChange).toHaveBeenCalledWith(['data'])
    })
  })

  it('reports an error when creating a category fails', async () => {
    const onCreate = vi.fn().mockRejectedValue(new Error('boom'))
    renderSelect({ onCreate })

    fireEvent.click(screen.getByLabelText('Filter by category'))
    fireEvent.change(screen.getByPlaceholderText('Add category...'), { target: { value: 'data' } })
    fireEvent.click(screen.getByLabelText('Add category'))

    await waitFor(() => {
      expect(screen.getByText('Failed to add category')).toBeInTheDocument()
    })
  })

  it('does not render the create input when onCreate is absent', () => {
    renderSelect()
    fireEvent.click(screen.getByLabelText('Filter by category'))
    expect(screen.queryByPlaceholderText('Add category...')).not.toBeInTheDocument()
  })

  it('filters the options as the search text changes', () => {
    renderSelect()
    fireEvent.click(screen.getByLabelText('Filter by category'))
    fireEvent.change(screen.getByLabelText('Search categories'), { target: { value: 'tech' } })

    expect(screen.getByText('technical')).toBeInTheDocument()
    expect(screen.queryByText('engineering')).not.toBeInTheDocument()
    expect(screen.queryByText('professional')).not.toBeInTheDocument()
  })

  it('shows a no-results message when the search matches nothing', () => {
    renderSelect()
    fireEvent.click(screen.getByLabelText('Filter by category'))
    fireEvent.change(screen.getByLabelText('Search categories'), { target: { value: 'zzz' } })

    expect(screen.getByText(/No categories match/)).toBeInTheDocument()
  })

  it('hides the search box when searchable is false', () => {
    renderSelect({ searchable: false })
    fireEvent.click(screen.getByLabelText('Filter by category'))
    expect(screen.queryByLabelText('Search categories')).not.toBeInTheDocument()
  })

  it('clears the search with the clear button', () => {
    renderSelect()
    fireEvent.click(screen.getByLabelText('Filter by category'))
    fireEvent.change(screen.getByLabelText('Search categories'), { target: { value: 'tech' } })
    fireEvent.click(screen.getByLabelText('Clear category search'))

    expect(screen.getByText('engineering')).toBeInTheDocument()
  })
})
