import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import RulesTab from './RulesTab'

vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children }: any) => <div>{children}</div>,
  closestCenter: vi.fn(),
  PointerSensor: vi.fn(),
  useSensor: vi.fn(),
  useSensors: vi.fn(() => ({})),
}))

vi.mock('@dnd-kit/sortable', () => ({
  SortableContext: ({ children }: any) => <div>{children}</div>,
  useSortable: () => ({ attributes: {}, listeners: {}, setNodeRef: vi.fn(), transform: null, transition: null, isDragging: false }),
  verticalListSortingStrategy: vi.fn(),
  arrayMove: vi.fn((arr) => arr),
}))

vi.mock('@dnd-kit/utilities', () => ({
  CSS: { Transform: { toString: () => '' } },
}))

const mockRules = {
  JOB: [
    { id: 'r1', key: 'remote_work', value: 'Remote work preferred', category: 'fit', scope: 'JOB', priority: 80, score_weight: 75, enabled: 1, description: 'Prefers remote' },
    { id: 'r2', key: 'salary_min', value: 'Min 80k', category: 'success', scope: 'JOB', priority: 60, score_weight: 50, enabled: 1 },
  ],
  SHARED: [
    { id: 'r3', key: 'visa_sponsorship', value: 'Must sponsor visa', category: 'fit', scope: 'SHARED', priority: 90, score_weight: 90, enabled: 1 },
  ],
}

describe('RulesTab', () => {
  it('renders Scoring Rules header', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getByText('Scoring Rules')).toBeInTheDocument()
  })

  it('renders rules count', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getByText(/3\/3 active/)).toBeInTheDocument()
  })

  it('renders rule keys', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getByText('remote_work')).toBeInTheDocument()
    expect(screen.getByText('salary_min')).toBeInTheDocument()
    expect(screen.getByText('visa_sponsorship')).toBeInTheDocument()
  })

  it('renders rule values', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getByText('Remote work preferred')).toBeInTheDocument()
    expect(screen.getByText('Min 80k')).toBeInTheDocument()
    expect(screen.getByText('Must sponsor visa')).toBeInTheDocument()
  })

  it('renders filter tabs', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getByText('All')).toBeInTheDocument()
    expect(screen.getAllByText('Shared').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Jobs')).toBeInTheDocument()
    expect(screen.getByText('Product Company')).toBeInTheDocument()
    expect(screen.getByText('Recruiting')).toBeInTheDocument()
  })

  it('renders scope columns', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getByText('Job Rules')).toBeInTheDocument()
    expect(screen.getByText('Shared Rules')).toBeInTheDocument()
  })

  it('renders Add rule button', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getAllByText('Add rule').length).toBeGreaterThan(0)
  })

  it('renders priority badges', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getByText('High')).toBeInTheDocument()
    expect(screen.getByText('Med')).toBeInTheDocument()
    expect(screen.getByText('Critical')).toBeInTheDocument()
  })

  it('renders loading state when rules is null', () => {
    render(<RulesTab rules={null} onUpdate={vi.fn()} />)
    expect(screen.getByText('Loading rules...')).toBeInTheDocument()
  })

  it('renders empty rule columns', () => {
    render(<RulesTab rules={{}} onUpdate={vi.fn()} />)
    expect(screen.getByText('Scoring Rules')).toBeInTheDocument()
  })

  it('renders category badges', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getAllByText('fit').length).toBeGreaterThan(0)
    expect(screen.getByText('success')).toBeInTheDocument()
  })

  it('renders scope badges', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getAllByText('Job').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Shared').length).toBeGreaterThan(0)
  })

  it('renders description', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    expect(screen.getByText('Prefers remote')).toBeInTheDocument()
  })
})
