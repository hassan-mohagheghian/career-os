import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import ConfirmDialog, { useConfirmDialog } from './ConfirmDialog'
import { act } from 'react'

function TestComponent({ onResult }) {
  const { dialog, showConfirm, onClose } = useConfirmDialog()
  return (
    <div>
      <button onClick={async () => {
        const result = await showConfirm('Test Title', 'Test Message', 'Confirm')
        onResult(result)
      }}>Show</button>
      <ConfirmDialog dialog={dialog} onClose={onClose} />
    </div>
  )
}

describe('ConfirmDialog', () => {
  it('returns null when dialog is null', () => {
    const { container } = render(<ConfirmDialog dialog={null} onClose={vi.fn()} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders title and message when dialog is provided', () => {
    const dialog = { title: 'Delete Item', message: 'Are you sure?', confirmLabel: 'Delete', variant: 'danger', resolve: vi.fn() }
    render(<ConfirmDialog dialog={dialog} onClose={vi.fn()} />)
    expect(screen.getByText('Delete Item')).toBeInTheDocument()
    expect(screen.getByText('Are you sure?')).toBeInTheDocument()
    expect(screen.getByText('Delete')).toBeInTheDocument()
  })

  it('calls resolve(true) when confirm button is clicked', () => {
    const resolve = vi.fn()
    const onClose = vi.fn()
    const dialog = { title: 'Title', message: 'Message', confirmLabel: 'OK', variant: 'danger', resolve }
    render(<ConfirmDialog dialog={dialog} onClose={onClose} />)
    fireEvent.click(screen.getByText('OK'))
    expect(resolve).toHaveBeenCalledWith(true)
    expect(onClose).toHaveBeenCalled()
  })

  it('calls resolve(false) when cancel is clicked', () => {
    const resolve = vi.fn()
    const onClose = vi.fn()
    const dialog = { title: 'Title', message: 'Message', confirmLabel: 'OK', variant: 'danger', resolve }
    render(<ConfirmDialog dialog={dialog} onClose={onClose} />)
    fireEvent.click(screen.getByText('Cancel'))
    expect(resolve).toHaveBeenCalledWith(false)
    expect(onClose).toHaveBeenCalled()
  })

  it('applies warning variant class', () => {
    const dialog = { title: 'Title', message: 'Msg', confirmLabel: 'OK', variant: 'warning', resolve: vi.fn() }
    render(<ConfirmDialog dialog={dialog} onClose={vi.fn()} />)
    const btn = screen.getByText('OK')
    expect(btn.className).toContain('bg-yellow-500')
  })

  it('applies info variant class (no special styling)', () => {
    const dialog = { title: 'Title', message: 'Msg', confirmLabel: 'OK', variant: 'info', resolve: vi.fn() }
    render(<ConfirmDialog dialog={dialog} onClose={vi.fn()} />)
    expect(screen.getByText('OK')).toBeInTheDocument()
  })

  it('applies default danger variant class', () => {
    const dialog = { title: 'Title', message: 'Msg', confirmLabel: 'Delete', variant: 'danger', resolve: vi.fn() }
    render(<ConfirmDialog dialog={dialog} onClose={vi.fn()} />)
    const btn = screen.getByText('Delete')
    expect(btn.className).toContain('bg-destructive')
  })
})

describe('useConfirmDialog', () => {
  it('returns dialog=null initially', () => {
    let result
    function Wrapper() {
      result = useConfirmDialog()
      return null
    }
    render(<Wrapper />)
    expect(result.dialog).toBeNull()
  })
})
