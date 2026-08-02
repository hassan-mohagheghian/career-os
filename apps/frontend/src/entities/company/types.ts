export interface Company {
  id: number
  name: string
  url: string | null
  location: string | null
  industry: string | null
  status: string
  current_node: string | null
  progress_pct: number
  error: string | null
  workflow_log: any
  fit_score: number | null
  success_score: number | null
  overall_score: number | null
  [key: string]: any
}
