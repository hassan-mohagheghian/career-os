import JobBaseCard from '@/shared/components/JobBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
  onReset?: () => void
  onViewWorkflow?: (item: any) => void
  onDragStart?: (e: React.DragEvent) => void
}

export default function JobQueuedCard({ item, onDelete, onProcess, onReset, onViewWorkflow, onDragStart }: Props) {
  return (
    <JobBaseCard
      item={item}
      dotColor="bg-yellow-400"
      statusText={<span className="text-yellow-500">queued</span>}
      onDelete={onDelete}
      onProcess={onProcess}
      onReset={onReset}
      onViewWorkflow={onViewWorkflow}
      onDragStart={onDragStart}
    />
  )
}
