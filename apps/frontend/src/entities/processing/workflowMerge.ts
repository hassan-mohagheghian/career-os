import type { WorkflowProgress, WorkflowStep } from './types'

function replaceInSteps(steps: WorkflowStep[], incoming: WorkflowStep): boolean {
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i]
    if (step.id === incoming.id || (step.node_id && incoming.node_id && step.node_id === incoming.node_id)) {
      steps[i] = incoming
      return true
    }
    if (step.children.length > 0 && replaceInSteps(step.children, incoming)) {
      return true
    }
  }
  return false
}

function recomputeProgress(steps: WorkflowStep[]): number {
  const displayable = steps.filter((step) => step.displayable)
  if (displayable.length === 0) return 0
  let total = 0
  for (const step of displayable) {
    if (step.status === 'completed' || step.status === 'failed' || step.status === 'skipped') {
      total += 100
    } else {
      total += step.progress ?? 0
    }
  }
  return Math.round((total / displayable.length) * 10) / 10
}

export function mergeWorkflowStep(workflow: WorkflowProgress, incoming: WorkflowStep): WorkflowProgress {
  const steps = workflow.steps.map((step) => ({ ...step, children: step.children.map((c) => ({ ...c })) }))
  replaceInSteps(steps, incoming)

  let currentStep = workflow.current_step
  if (currentStep && (currentStep.id === incoming.id || currentStep.node_id === incoming.node_id)) {
    currentStep = incoming
  }

  return {
    ...workflow,
    steps,
    current_step: currentStep,
    progress: recomputeProgress(steps),
  }
}
