export type ExecutionStatus = 'PENDING' | 'QUEUED' | 'STARTING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'

export type WorkflowStepStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'skipped'
export type WorkflowProgressStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface WorkflowStepError {
  code: string
  message: string
}

export interface WorkflowStep {
  id: string
  node_id: string | null
  title: string
  status: WorkflowStepStatus
  progress: number | null
  displayable: boolean
  children: WorkflowStep[]
  error: WorkflowStepError | null
  started_at: string | null
  completed_at: string | null
}

export interface WorkflowProgress {
  id: string
  name: string
  status: WorkflowProgressStatus
  current_step: WorkflowStep | null
  progress: number | null
  steps: WorkflowStep[]
}

export interface ProcessingExecution {
  id: string
  type: string
  status: ExecutionStatus
  target_id: string
  target_type: string
  created_at: string
  started_at: string | null
  finished_at: string | null
  retry_count: number
  error_message: string | null
}

export interface ProcessingExecutionDetail {
  execution_id: string
  job_id: string | null
  status: string
  created_at: string | null
  started_at: string | null
  completed_at: string | null
  error: { message: string } | null
  current_step: string | null
  workflow: WorkflowProgress | null
}

export interface QueueEntryLink {
  title?: string | null
  url: string
}

export interface QueueEntry {
  execution_id: string
  job_id: string
  title: string
  url: string | null
  links: QueueEntryLink[]
  status: string
  current_step: string | null
  progress: number | null
  error: string | null
  failed_step: string | null
  started_at: string | null
  finished_at: string | null
}

export interface QueueSnapshot {
  processing: QueueEntry[]
  queued: QueueEntry[]
  failed: QueueEntry[]
}

export interface SSEPayload {
  status: string
  step?: WorkflowStep
  updated_at?: string | null
  message?: string
  [key: string]: any
}

export interface SSEEventEnvelope {
  id: string
  type: string
  timestamp: string
  job_id: string | null
  execution_id: string
  payload: SSEPayload
}

export type SSEEventType =
  | 'execution.created'
  | 'execution.started'
  | 'execution.completed'
  | 'execution.failed'
  | 'execution.cancelled'
  | 'workflow.step.started'
  | 'workflow.step.progress'
  | 'workflow.step.completed'
  | 'workflow.step.failed'
  | 'queue.entry.removed'
