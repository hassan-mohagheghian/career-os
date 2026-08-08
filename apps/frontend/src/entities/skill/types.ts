export interface SkillListItem {
  id: number
  name: string
  level: number
  roles: string
  path: string
  category: string
  categories: string[]
  confidence: number | null
  market_relevance: number | null
  evidence: string | null
  tags: string[]
  aliases: string[]
  source_type: string
  mention_count: number
  pinned: boolean
  created_at: string | null
}

export interface Skill {
  id: number
  name: string
  level: number
  roles: string
  path: string
  category: string
  categories: string[]
  confidence: number | null
  market_relevance: number | null
  evidence: string | null
  tags: string[]
  aliases: string[]
  source_type: string
  mention_count?: number
  pinned?: boolean
  created_at: string | null
  [key: string]: unknown
}

export interface SkillSearchQuery {
  page_size?: number
  cursor?: string
  query?: string
  category?: string
  categories?: string[]
  pinned?: boolean
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
  categories?: string[]
}

export interface SkillUpdateInput {
  name?: string
  level?: number
  roles?: string
  path?: string
  category?: string
  categories?: string[]
  tags?: string[]
}

export type SkillSortField = 'created_at' | 'name' | 'level' | 'confidence' | 'market_relevance' | 'mention_count'

export interface SkillCategoryInfo {
  category: string
  count: number
  avg_demand: number | null
  avg_level: number | null
}

export const SKILL_CATEGORIES = ['technical', 'engineering', 'professional', 'domain', 'career'] as const

export type SkillCategory = (typeof SKILL_CATEGORIES)[number]
