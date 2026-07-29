import { Briefcase, Buildings, TreeStructure, FileText } from '@phosphor-icons/react'

export interface HistoryItemData {
  source: 'roadmap' | 'job-processing' | 'company-processing' | 'generation'
  title: string
  status: string
  started_at: string | null
  completed_at: string | null
  error: string | null
  session_id: string | null
  provider?: string | null
  id: number
}

export const SOURCE_CONFIG: Record<string, { icon: any; color: string; label: string }> = {
  'job-processing': { icon: Briefcase, color: 'bg-blue-500/15 text-blue-500', label: 'Job' },
  'company-processing': { icon: Buildings, color: 'bg-purple-500/15 text-purple-500', label: 'Company' },
  'generation': { icon: FileText, color: 'bg-cyan-500/15 text-cyan-500', label: 'Generate' },
  'roadmap': { icon: TreeStructure, color: 'bg-emerald-500/15 text-emerald-500', label: 'Roadmap' },
}

export const PROVIDER_LABELS: Record<string, string> = {
  'mimo': 'MiMo',
  'agent': 'Agent',
  'claude': 'Claude',
  'openai': 'OpenAI',
  'opencode': 'opencode',
}
