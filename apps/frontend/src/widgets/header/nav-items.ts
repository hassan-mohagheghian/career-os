import {
  Briefcase,
  Buildings,
  TreeStructure,
  FileText,
  Gear,
  Brain,
  UserCircle,
  type Icon,
} from '@phosphor-icons/react'

export interface NavChild {
  id: string
  label: string
}

export interface NavItem {
  id: string
  label: string
  icon: Icon
  color: string
  children?: NavChild[]
}

export const NAV_ITEMS: NavItem[] = [
  { id: 'jobs', label: 'Jobs', icon: Briefcase, color: 'text-blue-500' },
  { id: 'companies', label: 'Companies', icon: Buildings, color: 'text-emerald-500' },
  { id: 'candidate', label: 'Candidate', icon: UserCircle, color: 'text-violet-500' },
  { id: 'skills', label: 'Skills', icon: TreeStructure, color: 'text-amber-500' },
  { id: 'resume', label: 'Resume', icon: FileText, color: 'text-purple-500' },
  { id: 'rules', label: 'Rules', icon: Gear, color: 'text-cyan-500' },
  {
    id: 'ai',
    label: 'AI',
    icon: Brain,
    color: 'text-rose-500',
    children: [{ id: 'llm-configurations', label: 'LLM Configurations' }],
  },
]
