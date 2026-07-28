import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import WorkflowTerminal from './WorkflowTerminal'

const baseDrawer = {
  id: 1,
  company: 'Acme Corp',
  job_num: 42,
  status: 'processing',
  step_fetch: 1,
  step_validate: 1,
  step_extract_raw: 0,
  step_extract_struct: 0,
  step_summary: 0,
  step_analyze: 0,
  step_done: 0,
}

describe('WorkflowTerminal', () => {
  it('does not render when workflowDrawer is null', () => {
    const { container } = render(
      <WorkflowTerminal workflowDrawer={null} workflowLogs={[]} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument()
  })

  it('renders when workflowDrawer is provided', () => {
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={[]} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('Workflow Terminal')).toBeInTheDocument()
  })

  it('renders company badge', () => {
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={[]} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('Acme Corp #42')).toBeInTheDocument()
  })

  it('renders LIVE badge when processing', () => {
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={[]} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('● LIVE')).toBeInTheDocument()
  })

  it('renders waiting message when no logs', () => {
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={[]} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('Waiting for workflow output...')).toBeInTheDocument()
  })

  it('renders log entries', () => {
    const logs = [
      { step: 'fetch', msg: 'Fetching page...', ts: '10:00:00' },
      { step: 'out', msg: 'Page loaded', ts: '10:00:01' },
    ]
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={logs} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('Fetching page...')).toBeInTheDocument()
    expect(screen.getByText('Page loaded')).toBeInTheDocument()
  })

  it('renders error log entries', () => {
    const logs = [
      { step: 'err', msg: 'Connection failed', ts: '10:00:00' },
    ]
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={logs} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('Connection failed')).toBeInTheDocument()
  })

  it('renders cmd log entries', () => {
    const logs = [
      { step: 'cmd', msg: 'python script.py', ts: '10:00:00' },
    ]
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={logs} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('python script.py')).toBeInTheDocument()
  })

  it('renders step log entries', () => {
    const logs = [
      { step: 'step', msg: 'Step started', ts: '10:00:00' },
    ]
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={logs} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('Step started')).toBeInTheDocument()
  })

  it('renders done log entries', () => {
    const logs = [
      { step: 'done', msg: 'Complete: Acme #1', ts: '10:00:00' },
    ]
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={logs} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('Complete: Acme #1')).toBeInTheDocument()
  })

  it('renders error type log entries', () => {
    const logs = [
      { step: 'error', msg: 'Something failed', ts: '10:00:00' },
    ]
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={logs} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('Something failed')).toBeInTheDocument()
  })

  it('renders mimo log entries', () => {
    const logs = [
      { step: 'mimo', msg: 'AI reasoning...', ts: '10:00:00' },
    ]
    render(
      <WorkflowTerminal workflowDrawer={baseDrawer} workflowLogs={logs} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.getByText('AI reasoning...')).toBeInTheDocument()
  })

  it('does not render LIVE badge when not processing', () => {
    render(
      <WorkflowTerminal workflowDrawer={{ ...baseDrawer, status: 'done' }} workflowLogs={[]} workflowEndRef={{ current: null }} onClose={vi.fn()} />
    )
    expect(screen.queryByText('● LIVE')).not.toBeInTheDocument()
  })
})
