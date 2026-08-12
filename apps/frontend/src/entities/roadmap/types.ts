export type RoadmapStatus = 'ACTIVE' | 'COMPLETED' | 'ARCHIVED'

export type RoadmapSource = 'APPLICATION' | 'AI_GENERATED' | 'MANUAL'

export type GoalType = 'JOB' | 'CAREER' | 'SKILL' | 'CUSTOM'

export type NodePriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export type TaskStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'SKIPPED'

export type MilestoneStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED'

export type ResourceType =
  | 'ARTICLE'
  | 'VIDEO'
  | 'COURSE'
  | 'BOOK'
  | 'DOCUMENTATION'
  | 'PROJECT'
  | 'OTHER'

export type ResourceStatus = 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED'

export type ResourceSource = 'AI' | 'USER'

export interface RoadmapGoal {
  id: string
  roadmap_id: string
  type: GoalType
  title: string
  description: string
  target_job_id: string | null
  target_company_id: string | null
  target_skill_id: string | null
}

export interface RoadmapSkillLink {
  id: string
  roadmap_id: string
  milestone_id: string | null
  task_id: string | null
  skill_id: string
  skill_name: string
}

export interface RoadmapTask {
  id: string
  milestone_id: string
  position: number
  title: string
  description: string
  status: TaskStatus
  priority: NodePriority
  estimated_effort: string | null
  success_criteria: string | null
  completed_at: string | null
  skills: RoadmapSkillLink[]
}

export interface RoadmapMilestone {
  id: string
  roadmap_id: string
  position: number
  title: string
  description: string
  status: MilestoneStatus
  priority: NodePriority
  tasks: RoadmapTask[]
  skills: RoadmapSkillLink[]
}

export interface RoadmapNote {
  id: string
  roadmap_id: string
  milestone_id: string | null
  task_id: string | null
  content: string
  created_at: string | null
}

export interface RoadmapResource {
  id: string
  roadmap_id: string
  milestone_id: string | null
  task_id: string | null
  title: string
  url: string
  description: string
  type: ResourceType
  status: ResourceStatus
  source: ResourceSource
  created_at: string | null
}

export interface MilestoneProgress {
  milestone_id: string
  completed: number
  total: number
  percent: number
}

export interface RoadmapProgress {
  completed_tasks: number
  total_tasks: number
  overall_percent: number
  milestone_progress: MilestoneProgress[]
}

export interface RoadmapSummary {
  id: string
  title: string
  description: string
  goal_type: GoalType
  source: RoadmapSource
  application_id: string | null
  status: RoadmapStatus
  progress: RoadmapProgress
  created_at: string | null
  updated_at: string | null
}

export interface RoadmapDetail extends RoadmapSummary {
  goal: RoadmapGoal | null
  milestones: RoadmapMilestone[]
  notes: RoadmapNote[]
  resources: RoadmapResource[]
}

export interface DeleteResponse {
  status: string
}

export interface CreateRoadmapInput {
  title?: string
  description?: string
  goal?: {
    type?: GoalType
    title?: string
    description?: string
  }
}

export interface UpdateRoadmapInput {
  title?: string
  description?: string
  status?: RoadmapStatus
  goal?: RoadmapGoal
}

export interface CreateMilestoneInput {
  title?: string
  description?: string
  priority?: NodePriority
}

export interface UpdateMilestoneInput {
  position?: number
  title?: string
  description?: string
  status?: MilestoneStatus
  priority?: NodePriority
}

export interface CreateTaskInput {
  title?: string
  description?: string
  priority?: NodePriority
  estimated_effort?: string | null
  success_criteria?: string | null
}

export interface UpdateTaskInput {
  position?: number
  title?: string
  description?: string
  status?: TaskStatus
  priority?: NodePriority
  estimated_effort?: string | null
  success_criteria?: string | null
}

export interface CreateNoteInput {
  content?: string
  milestone_id?: string | null
  task_id?: string | null
}

export interface CreateResourceInput {
  title?: string
  url?: string
  description?: string
  type?: ResourceType
  milestone_id?: string | null
  task_id?: string | null
}

export interface UpdateResourceInput {
  title?: string
  url?: string
  description?: string
  type?: ResourceType
  status?: ResourceStatus
}