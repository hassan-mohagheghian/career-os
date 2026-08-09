import { scoreColor } from '@/shared/lib/grade'

interface CompanyScoreCardProps {
  label: string
  value: number
}

export function CompanyScoreCard({ label, value }: CompanyScoreCardProps) {
  return (
    <div className="flex flex-col items-center">
      <div className={`text-lg font-bold ${scoreColor(value)}`}>{value}</div>
      <div className="text-2xs uppercase tracking-wider text-muted-foreground font-semibold">{label}</div>
    </div>
  )
}
