export interface SkillListItem {
  id: number
  name: string
  level: number
  roles: string
  path: string
  category: string
  confidence: number | null
  market_relevance: number | null
  evidence: string | null
  tags: string[]
  aliases: string[]
  created_at: string | null
}

export interface Skill {
  id: number
  name: string
  level: number
  roles: string
  path: string
  category: string
  confidence: number | null
  market_relevance: number | null
  evidence: string | null
  tags: string[]
  aliases: string[]
  created_at: string | null
  [key: string]: unknown
}

export interface SkillSearchQuery {
  page_size?: number
  cursor?: string
  query?: string
  category?: string
  sort?: string
  order?: 'asc' | 'desc'
}

export interface InfiniteSkillSearchResult {
  items: SkillListItem[]
  next_cursor: string | null
  has_more: boolean
  total_items: number
}

export interface SkillCreateInput {
  name: string
  level: number
  roles?: string
  path?: string
  category?: string
}

export interface SkillUpdateInput {
  name?: string
  level?: number
  roles?: string
  path?: string
  category?: string
  tags?: string[]
}

export type SkillSortField = 'created_at' | 'name' | 'level' | 'confidence' | 'market_relevance'

export const SKILL_CATEGORIES = ['technical', 'engineering', 'professional', 'domain', 'career'] as const

export type SkillCategory = (typeof SKILL_CATEGORIES)[number]
