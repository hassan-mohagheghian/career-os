interface CompanyScoreCardProps {
  label: string
  value: number
}

function scoreColor(value: number): string {
  if (value >= 80) return 'text-emerald-500'
  if (value >= 60) return 'text-blue-500'
  if (value >= 40) return 'text-yellow-500'
  return 'text-red-500'
}

export function CompanyScoreCard({ label, value }: CompanyScoreCardProps) {
  return (
    <div className="flex flex-col items-center">
      <div className={`text-lg font-bold ${scoreColor(value)}`}>{value}</div>
      <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">{label}</div>
    </div>
  )
}
