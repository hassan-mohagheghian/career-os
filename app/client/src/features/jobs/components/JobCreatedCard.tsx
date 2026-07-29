import JobBaseCard from '@/shared/components/JobBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
  onViewWorkflow?: (item: any) => void
  onDragStart?: (e: React.DragEvent) => void
}

export default function JobCreatedCard({ item, onDelete, onProcess, onViewWorkflow, onDragStart }: Props) {
  return (
    <JobBaseCard
      item={item}
      dotColor="bg-muted-foreground"
      statusText={<span className="text-gray-400">created</span>}
      onDelete={onDelete}
      onProcess={onProcess}
      onViewWorkflow={onViewWorkflow}
      onDragStart={onDragStart}
    />
  )
}
