export const ACTIVE_STATUSES = new Set(['starting', 'fetching', 'analyzing', 'generating', 'finalizing'])

export const STATUS_LABELS: Record<string, string> = {
  created: 'Created',
  queued: 'Queued',
  waiting: 'Waiting',
  starting: 'Starting...',
  fetching: 'Fetching...',
  analyzing: 'Analyzing...',
  generating: 'Generating...',
  finalizing: 'Finalizing...',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
}
