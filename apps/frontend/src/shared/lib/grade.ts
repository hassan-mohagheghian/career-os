const GRADE_BUCKETS: Array<[number, string]> = [
  [90, 'A++'],
  [80, 'A+'],
  [70, 'A'],
  [50, 'B'],
  [30, 'C'],
  [0, 'D'],
]

export function gradeForScore(score: number | null | undefined): string {
  if (score === null || score === undefined || Number.isNaN(score)) return 'P'
  for (const [threshold, grade] of GRADE_BUCKETS) {
    if (score >= threshold) return grade
  }
  return 'P'
}

export function scoreColor(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 'text-muted-foreground'
  }
  if (value >= 90) return 'text-green-500'
  if (value >= 70) return 'text-emerald-500'
  if (value >= 50) return 'text-yellow-500'
  if (value >= 30) return 'text-orange-500'
  return 'text-red-500'
}
