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
