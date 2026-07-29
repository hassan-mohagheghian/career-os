import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { CheckCircle } from '@phosphor-icons/react'
import StepProgress from './StepProgress'

vi.mock('@/shared/ui/tooltip', () => ({
  TooltipProvider: ({ children }: any) => <>{children}</>,
  Tooltip: ({ children }: any) => <>{children}</>,
  TooltipTrigger: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
}))

const STEPS = [
  { key: 'a', icon: <CheckCircle className="w-3 h-3" />, label: 'Step A' },
  { key: 'b', icon: <CheckCircle className="w-3 h-3" />, label: 'Step B' },
  { key: 'c', icon: <CheckCircle className="w-3 h-3" />, label: 'Step C' },
]

describe('StepProgress', () => {
  it('renders all steps', () => {
    render(<StepProgress steps={STEPS} values={[0, 0, 0]} nextStep={0} />)
    expect(screen.getByText('Step A — in progress...')).toBeInTheDocument()
    expect(screen.getByText('Step B')).toBeInTheDocument()
    expect(screen.getByText('Step C')).toBeInTheDocument()
  })

  it('marks completed steps', () => {
    render(<StepProgress steps={STEPS} values={[1, 1, 0]} nextStep={2} />)
    expect(screen.getByText('Step A — done')).toBeInTheDocument()
    expect(screen.getByText('Step B — done')).toBeInTheDocument()
    expect(screen.getByText('Step C — in progress...')).toBeInTheDocument()
  })
})
