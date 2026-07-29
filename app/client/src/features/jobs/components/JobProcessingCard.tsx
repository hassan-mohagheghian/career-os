import { ACTIVE_STATUSES, STATUS_LABELS } from '@/shared/lib/statusConfig'
import JobBaseCard from '@/shared/components/JobBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onCancel?: () => void
  onReset?: () => void
  onViewWorkflow?: (item: any) => void
  onDragStart?: (e: React.DragEvent) => void
}

export default function JobProcessingCard({ item, onDelete, onCancel, onReset, onViewWorkflow, onDragStart }: Props) {
  const label = STATUS_LABELS[item.status] || 'Processing...'
  const color = ACTIVE_STATUSES.has(item.status) ? 'text-blue-500' : 'text-muted-foreground'

  return (
    <JobBaseCard
      item={item}
      dotColor="bg-blue-500 animate-pulse"
      statusText={<span className={color}>{label}</span>}
      onDelete={onDelete}
      onCancel={onCancel}
      onReset={onReset}
      onViewWorkflow={onViewWorkflow}
      onDragStart={onDragStart}
    />
  )
}
