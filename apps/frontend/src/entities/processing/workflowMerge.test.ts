import { describe, it, expect } from 'vitest'
import { mergeWorkflowStep } from './workflowMerge'
import type { WorkflowProgress, WorkflowStep } from './types'

const step = (overrides: Partial<WorkflowStep> = {}): WorkflowStep => ({
  id: 'step-1',
  node_id: 'load_job',
  title: 'Load Job',
  status: 'pending',
  progress: null,
  displayable: true,
  children: [],
  error: null,
  started_at: null,
  completed_at: null,
  ...overrides,
})

function buildWorkflow(): WorkflowProgress {
  return {
    id: 'wf-1',
    name: 'Job Context Preparation',
    status: 'running',
    current_step: null,
    progress: 0,
    steps: [
      step(),
      step({
        id: 'step-2',
        node_id: 'fetch_sources',
        title: 'Fetch Sources',
        children: [
          step({ id: 'source_0', node_id: 'source_0', title: 'LinkedIn', status: 'pending' }),
          step({ id: 'source_1', node_id: 'source_1', title: 'Company Site', status: 'pending' }),
        ],
      }),
    ],
  }
}

describe('mergeWorkflowStep', () => {
  it('replaces a top-level step by node_id and preserves siblings', () => {
    const workflow = buildWorkflow()
    const incoming = step({ status: 'completed', progress: 100 })
    const merged = mergeWorkflowStep(workflow, incoming)

    expect(merged.steps).toHaveLength(2)
    expect(merged.steps[0].status).toBe('completed')
    expect(merged.steps[0].progress).toBe(100)
    expect(merged.steps[1].title).toBe('Fetch Sources')
  })

  it('replaces a top-level step by id', () => {
    const workflow = buildWorkflow()
    const incoming = step({ id: 'step-1', status: 'failed', error: { code: 'X', message: 'boom' } })
    const merged = mergeWorkflowStep(workflow, incoming)

    expect(merged.steps[0].status).toBe('failed')
    expect(merged.steps[0].error?.message).toBe('boom')
  })

  it('updates a nested child step and keeps the rest intact', () => {
    const workflow = buildWorkflow()
    const incoming = step({ id: 'source_0', node_id: 'source_0', title: 'LinkedIn', status: 'processing', progress: 50 })
    const merged = mergeWorkflowStep(workflow, incoming)

    const fetch = merged.steps[1]
    expect(fetch.children[0].status).toBe('processing')
    expect(fetch.children[0].progress).toBe(50)
    expect(fetch.children[1].status).toBe('pending')
  })

  it('returns an unchanged deep copy when the step is not found', () => {
    const workflow = buildWorkflow()
    const incoming = step({ id: 'unknown', node_id: 'unknown', title: 'Nope' })
    const merged = mergeWorkflowStep(workflow, incoming)

    expect(merged.steps[0].title).toBe('Load Job')
    expect(merged.steps[1].children).toHaveLength(2)
  })

  it('does not mutate the original workflow object', () => {
    const workflow = buildWorkflow()
    const incoming = step({ status: 'completed', progress: 100 })
    mergeWorkflowStep(workflow, incoming)

    expect(workflow.steps[0].status).toBe('pending')
    expect(workflow.steps[0].progress).toBeNull()
  })

  it('updates current_step when it matches the incoming step', () => {
    const workflow = buildWorkflow()
    workflow.current_step = step({ node_id: 'load_job' })
    const incoming = step({ status: 'processing', progress: 10 })
    const merged = mergeWorkflowStep(workflow, incoming)

    expect(merged.current_step?.status).toBe('processing')
    expect(merged.current_step?.node_id).toBe('load_job')
  })

  it('recomputes the overall progress from displayable steps', () => {
    const workflow = buildWorkflow()
    const incoming = step({ status: 'completed', progress: 100 })
    const merged = mergeWorkflowStep(workflow, incoming)

    expect(merged.progress).toBe(50)
  })

  it('advances overall progress with partial step progress', () => {
    const workflow = buildWorkflow()
    const incoming = step({ status: 'processing', progress: 42.5 })
    const merged = mergeWorkflowStep(workflow, incoming)

    expect(merged.progress).toBe(21.3)
  })

  it('counts failed and skipped steps as complete', () => {
    const workflow = buildWorkflow()
    const failed = mergeWorkflowStep(workflow, step({ status: 'failed', progress: 0 }))
    expect(failed.progress).toBe(50)

    const skipped = buildWorkflow()
    const mergedSkipped = mergeWorkflowStep(skipped, step({ status: 'skipped', progress: 0 }))
    expect(mergedSkipped.progress).toBe(50)
  })
})
