import { Lightning, ListChecks, Gift } from '@phosphor-icons/react'
import { TabHeader } from '@/shared/components/DrawerComponents'

export default function StructuredTab({ job }) {
  let sd = null; try { sd = job.structured_description ? JSON.parse(job.structured_description) : null } catch {}
  if (!sd) return <div className="text-xs py-4 text-center text-muted-foreground">No structured data available</div>
  return (
    <div>
      {sd.requirements?.length > 0 && (
        <div className="mb-3">
          <TabHeader title="Requirements" />
          <ul className="text-sm space-y-1">{sd.requirements.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><ListChecks className="w-3 h-3 shrink-0 mt-0.5 text-green-500" /><span>{r}</span></li>)}</ul>
        </div>
      )}
      {sd.responsibilities?.length > 0 && (
        <div className="mb-3">
          <TabHeader title="Responsibilities" />
          <ul className="text-sm space-y-1">{sd.responsibilities.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Lightning className="w-3 h-3 shrink-0 mt-0.5 text-primary" /><span>{r}</span></li>)}</ul>
        </div>
      )}
      {sd.benefits?.length > 0 && (
        <div className="mb-3">
          <TabHeader title="Benefits" />
          <ul className="text-sm space-y-1">{sd.benefits.map((r, i) => <li key={i} className="flex items-start gap-2 text-muted-foreground"><Gift className="w-3 h-3 shrink-0 mt-0.5 text-purple-500" /><span>{r}</span></li>)}</ul>
        </div>
      )}
    </div>
  )
}
