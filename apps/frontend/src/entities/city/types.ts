export interface CityListItem {
  id: string
  city: string
  country: string
  original_text?: string | null
  address?: string | null
  aliases: string[]
  job_count: number
  created_at?: string | null
  updated_at?: string | null
}

export interface CitySearchQuery {
  query?: string
  sort?: 'jobs' | 'country' | 'city' | 'created_at'
  order?: 'asc' | 'desc'
  page_size?: number
  cursor?: string
}

export interface CityListResponse {
  items: CityListItem[]
  next_cursor: string | null
  has_more: boolean
  total_items: number
}

export interface InfiniteCitySearchResult {
  items: CityListItem[]
  next_cursor: string | null
  has_more: boolean
  total_items: number
}