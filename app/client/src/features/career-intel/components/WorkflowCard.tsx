import { CheckCircle, Circle, Spinner, Warning } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Card } from '@/shared/ui/card'

const STEP_LABELS = {
  pending: 'Queued',
  processing: 'Generating...',
  completed: 'Complete',
  failed: 'Failed',
}

function StepIcon({ status }) {
  if (status === 'completed') return <CheckCircle className="w-3.5 h-3.5 text-green-500" />
  if (status === 'processing') return <Spinner className="w-3.5 h-3.5 text-primary animate-spin" />
  if (status === 'failed') return <Warning className="w-3.5 h-3.5 text-red-500" />
  return <Circle className="w-3.5 h-3.5 text-muted-foreground/40" />
}

export default function WorkflowCard({ section, status }) {
  const st = status || {}
  const steps = [
    { label: 'Collecting data', status: st.status === 'processing' ? 'processing' : st.status === 'completed' ? 'completed' : 'pending' },
    { label: 'AI analysis', status: st.status === 'processing' ? 'pending' : st.status === 'completed' ? 'completed' : 'pending' },
    { label: 'Calculating metrics', status: st.status === 'completed' ? 'completed' : 'pending' },
    { label: 'Saving results', status: st.status === 'completed' ? 'completed' : st.status === 'failed' ? 'failed' : 'pending' },
  ]

  return (
    <Card className="p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="font-bold text-xs capitalize">{section}</span>
        <span className={cn("text-[0.5rem] font-semibold",
          st.status === 'completed' ? 'text-green-500' :
          st.status === 'processing' ? 'text-primary' :
          st.status === 'failed' ? 'text-red-500' : 'text-muted-foreground'
        )}>{STEP_LABELS[st.status] || 'Unknown'}</span>
      </div>
      <div className="space-y-1.5">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-2">
            <StepIcon status={step.status} />
            <span className={cn("text-[0.55rem]",
              step.status === 'completed' ? 'text-foreground' :
              step.status === 'processing' ? 'text-primary font-semibold' : 'text-muted-foreground'
            )}>{step.label}</span>
          </div>
        ))}
      </div>
      {st.error && (
        <div className="mt-2 text-[0.5rem] text-red-500 p-1.5 rounded bg-red-500/5">{st.error}</div>
      )}
    </Card>
  )
}
