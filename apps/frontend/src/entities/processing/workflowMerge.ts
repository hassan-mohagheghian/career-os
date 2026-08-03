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
  }
}
