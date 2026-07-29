export function setSearchParam(key: string, value: string | null) {
  const url = new URL(window.location.href)
  if (value) {
    url.searchParams.set(key, value)
  } else {
    url.searchParams.delete(key)
  }
  window.history.replaceState({}, '', url.toString())
}

export function getSearchParam(key: string): string | null {
  if (typeof window === 'undefined') return null
  const url = new URL(window.location.href)
  return url.searchParams.get(key)
}
