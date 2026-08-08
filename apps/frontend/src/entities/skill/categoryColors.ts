const CANONICAL_COLORS: Record<string, string> = {
  technical: 'text-blue-500 bg-blue-500/10',
  engineering: 'text-green-500 bg-green-500/10',
  professional: 'text-purple-500 bg-purple-500/10',
  domain: 'text-orange-500 bg-orange-500/10',
  career: 'text-cyan-500 bg-cyan-500/10',
}

const PALETTE = [
  'text-rose-500 bg-rose-500/10',
  'text-amber-500 bg-amber-500/10',
  'text-emerald-500 bg-emerald-500/10',
  'text-teal-500 bg-teal-500/10',
  'text-sky-500 bg-sky-500/10',
  'text-indigo-500 bg-indigo-500/10',
  'text-fuchsia-500 bg-fuchsia-500/10',
  'text-lime-500 bg-lime-500/10',
]

function hashCode(input: string): number {
  let hash = 0
  for (let i = 0; i < input.length; i += 1) {
    hash = (hash << 5) - hash + input.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

export function categoryColorClass(category: string): string {
  const key = category.toLowerCase()
  if (CANONICAL_COLORS[key]) return CANONICAL_COLORS[key]
  return PALETTE[hashCode(key) % PALETTE.length]
}
