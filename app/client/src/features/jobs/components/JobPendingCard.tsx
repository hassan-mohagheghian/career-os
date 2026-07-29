import JobBaseCard from '@/shared/components/JobBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
  onReset?: () => void
  onViewWorkflow?: (item: any) => void
  onDragStart?: (e: React.DragEvent) => void
}

export default function JobPendingCard({ item, onDelete, onProcess, onReset, onViewWorkflow, onDragStart }: Props) {
  return (
    <JobBaseCard
      item={item}
      dotColor="bg-muted-foreground"
      statusText={<span className="text-gray-400">created</span>}
      onDelete={onDelete}
      onProcess={onProcess}
      onReset={onReset}
      onViewWorkflow={onViewWorkflow}
      onDragStart={onDragStart}
    />
  )
}
