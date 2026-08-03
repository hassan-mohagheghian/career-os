export const PAGE_SIZE = 30
export const API_BASE = '/api'
export const WORKFLOW_WS_PORT = 8765
export const SORT_FIELDS = ['created_at', 'overall_score', 'fit_score', 'success_score', 'company', 'location', 'applicants', 'posted_at', 'apply_time', 'response_time'] as const
export type SortField = typeof SORT_FIELDS[number]
