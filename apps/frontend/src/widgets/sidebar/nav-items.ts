import {
  Briefcase,
  Buildings,
  TreeStructure,
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
  children?: NavChild[]
}

export const NAV_ITEMS: NavItem[] = [
  { id: 'jobs', label: 'Jobs', icon: Briefcase },
  { id: 'companies', label: 'Companies', icon: Buildings },
  { id: 'skills', label: 'Skills', icon: TreeStructure },
  { id: 'candidate', label: 'Candidate', icon: UserCircle },
  { id: 'rules', label: 'Rules', icon: Gear },
  {
    id: 'ai',
    label: 'AI',
    icon: Brain,
    children: [{ id: 'llm-configurations', label: 'LLM Configurations' }],
  },
]
