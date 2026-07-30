export const ACTIVE_STATUSES = new Set(['processing'])

export const STATUS_LABELS: Record<string, string> = {
  created: 'Created',
  pending: 'Pending',
  queued: 'Queued',
  processing: 'Processing...',
  processed: 'Processed',
  imported: 'Imported',
  failed: 'Failed',
  cancelled: 'Cancelled',
}
