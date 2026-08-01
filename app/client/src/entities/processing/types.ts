export type ExecutionStatus = 'PENDING' | 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'

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

export interface SSEEvent {
  execution_id: string
  job_id: string
  status: string
  current_step: string | null
  progress: number | null
  message: string | null
  updated_at: string
}

export type SSEEventType =
  | 'ExecutionQueued'
  | 'ExecutionStarted'
  | 'ExecutionStepChanged'
  | 'ExecutionCompleted'
  | 'ExecutionFailed'
