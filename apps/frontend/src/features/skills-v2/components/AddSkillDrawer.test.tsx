import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import AddSkillDrawer from './AddSkillDrawer'

vi.mock('@/entities/skill/hooks', () => ({
  useSkillCategories: () => ({
    categories: [
      { category: 'technical', count: 1, avg_demand: null, avg_level: null },
      { category: 'engineering', count: 1, avg_demand: null, avg_level: null },
    ],
    isLoading: false,
    createMutation: { mutateAsync: vi.fn().mockResolvedValue({ id: 9, name: 'data', created: true }) },
    deleteMutation: { mutateAsync: vi.fn() },
  }),
}))

describe('AddSkillDrawer', () => {
  it('submits skill data when name is filled', () => {
    const onSubmit = vi.fn()
    render(
      <AddSkillDrawer open onSubmit={onSubmit} onOpenChange={vi.fn()} />
    )

    fireEvent.change(screen.getByPlaceholderText('e.g. Kubernetes'), {
      target: { value: 'Kafka' },
    })
    fireEvent.click(screen.getByRole('button', { name: /add skill/i }))

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Kafka', categories: [] })
    )
  })

  it('submits the selected categories', () => {
    const onSubmit = vi.fn()
    render(
      <AddSkillDrawer open onSubmit={onSubmit} onOpenChange={vi.fn()} />
    )

    fireEvent.change(screen.getByPlaceholderText('e.g. Kubernetes'), {
      target: { value: 'Kafka' },
    })
    fireEvent.click(screen.getByLabelText('Filter by category'))
    fireEvent.click(screen.getByText('technical'))
    fireEvent.click(screen.getByRole('button', { name: /add skill/i }))

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ categories: ['technical'], category: 'technical' })
    )
  })

  it('does not submit when name is empty', () => {
    const onSubmit = vi.fn()
    render(
      <AddSkillDrawer open onSubmit={onSubmit} onOpenChange={vi.fn()} />
    )

    fireEvent.click(screen.getByRole('button', { name: /add skill/i }))
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('closes via Cancel', () => {
    const onSubmit = vi.fn()
    const onOpenChange = vi.fn()
    render(
      <AddSkillDrawer open onSubmit={onSubmit} onOpenChange={onOpenChange} />
    )

    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
})
