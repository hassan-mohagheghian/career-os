export interface Skill {
  id: number
  name: string
  category: string
  [key: string]: any
}

export interface SkillRoadmapProgress {
  [skillName: string]: any
}

export interface DashboardData {
  [key: string]: any
}
