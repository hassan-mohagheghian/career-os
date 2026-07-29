import JobBaseCard from '@/shared/components/JobBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
  onMoveToCreated?: () => void
  onViewWorkflow?: (item: any) => void
  onDragStart?: (e: React.DragEvent) => void
}

export default function JobPendingCard({ item, onDelete, onProcess, onMoveToCreated, onViewWorkflow, onDragStart }: Props) {
  return (
    <JobBaseCard
      item={item}
      dotColor="bg-sky-400"
      statusText={<span className="text-sky-500">pending</span>}
      onDelete={onDelete}
      onProcess={onProcess}
      onMoveToCreated={onMoveToCreated}
      onViewWorkflow={onViewWorkflow}
      onDragStart={onDragStart}
    />
  )
}
