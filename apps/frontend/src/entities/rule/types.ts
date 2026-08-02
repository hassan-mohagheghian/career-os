export interface Rule {
  id: number
  priority: number
  field: string
  operator: string
  value: string
  action: string
  enabled: boolean
  [key: string]: any
}
