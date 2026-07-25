import { TabHeader } from '@/components/DrawerComponents'

export default function SummaryTab({ summary }) {
  if (!summary) return <div className="text-xs py-4 text-center text-muted-foreground">No summary available</div>
  return (
    <div>
      <div className="mb-3">
        <TabHeader title="Summary" />
        <p className="text-sm text-muted-foreground">{summary.summary}</p>
      </div>
      <div className="mb-3">
        <TabHeader title="Stack Required" />
        <p className="text-sm text-muted-foreground">{summary.stack}</p>
      </div>
      <div className="mb-3">
        <TabHeader title="Resume Fit" />
        <p className="text-sm text-muted-foreground">{summary.resumeFit}</p>
      </div>
      <div className="mb-3">
        <TabHeader title="Note" />
        <p className="text-sm font-semibold" style={{ color: ['A','A+','A++'].includes(summary.score) ? '#22c55e' : ['B','C'].includes(summary.score) ? '#eab308' : '#ef4444' }}>{summary.note}</p>
      </div>
    </div>
  )
}
