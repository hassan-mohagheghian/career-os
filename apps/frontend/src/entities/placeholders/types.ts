export interface PlaceholderKeyInfo {
  key: string
  label: string
}

export interface PlaceholderItem {
  key: string
  value: string
  updated_at: string | null
}

export interface PlaceholdersList {
  keys: PlaceholderKeyInfo[]
  items: PlaceholderItem[]
  values: Record<string, string>
}

export type PlaceholderValues = Record<string, string>