export function formatCityLocation(city?: string | null, country?: string | null): string {
  const parts = [city, country].filter(Boolean)
  return parts.join(', ')
}