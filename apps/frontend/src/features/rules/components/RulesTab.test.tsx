import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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

vi.mock('@/shared/components/Drawer', () => ({
  Drawer: ({ open, children }: any) => (open ? <div data-testid="rule-drawer">{children}</div> : null),
  DrawerHeader: ({ title, onClose }: any) => (
    <div>
      <div>{title}</div>
      <button onClick={onClose} aria-label="Close">x</button>
    </div>
  ),
  DrawerContent: ({ children }: any) => <div>{children}</div>,
  DrawerFooter: ({ children }: any) => <div>{children}</div>,
}))

vi.mock('@/shared/ui/select', () => ({
  Select: ({ children }: any) => <div>{children}</div>,
  SelectTrigger: ({ children }: any) => <div>{children}</div>,
  SelectValue: () => <span />,
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children }: any) => <div>{children}</div>,
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

  it('opens the Add Rule drawer from the bottom when clicking Add rule', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    fireEvent.click(screen.getAllByText('Add rule')[0])
    expect(screen.getByText('Add Rule')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('e.g. remote_work')).toBeInTheDocument()
  })

  it('closes the drawer on close', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    fireEvent.click(screen.getAllByText('Add rule')[0])
    expect(screen.getByText('Add Rule')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Close'))
    expect(screen.queryByText('Add Rule')).not.toBeInTheDocument()
  })

  it('adds a rule and refreshes when saving from the drawer', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true })
    global.fetch = fetchMock as any
    const onUpdate = vi.fn()
    render(<RulesTab rules={mockRules} onUpdate={onUpdate} />)

    fireEvent.click(screen.getAllByText('Add rule')[0])
    fireEvent.change(screen.getByPlaceholderText('e.g. remote_work'), { target: { value: 'new_rule' } })
    fireEvent.change(screen.getByPlaceholderText('How the rule matches candidates / companies'), { target: { value: 'Some value' } })
    fireEvent.click(screen.getByText('Save'))

    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    expect(fetchMock).toHaveBeenCalledWith('/api/rules', expect.objectContaining({ method: 'POST' }))
    await waitFor(() => expect(onUpdate).toHaveBeenCalled())
    expect(screen.queryByText('Add Rule')).not.toBeInTheDocument()
  })

  it('opens the Edit Rule drawer prefilled with the rule', () => {
    render(<RulesTab rules={mockRules} onUpdate={vi.fn()} />)
    fireEvent.click(screen.getAllByTitle('Edit')[0])
    expect(screen.getByText('Edit Rule')).toBeInTheDocument()
    expect(screen.getByDisplayValue('visa_sponsorship')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Must sponsor visa')).toBeInTheDocument()
  })
})
