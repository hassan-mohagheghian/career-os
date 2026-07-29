import JobBaseCard from '@/shared/components/JobBaseCard'

interface Props {
  item: any
  onCancel?: () => void
  onViewWorkflow?: (item: any) => void
  onDragStart?: (e: React.DragEvent) => void
}

export default function JobProcessingCard({ item, onCancel, onViewWorkflow, onDragStart }: Props) {
  return (
    <JobBaseCard
      item={item}
      dotColor="bg-blue-500 animate-pulse"
      statusText={<span className="text-blue-500">Processing...</span>}
      onCancel={onCancel}
      onViewWorkflow={onViewWorkflow}
      onDragStart={onDragStart}
    />
  )
}
