import { Warning } from '@phosphor-icons/react'
import JobBaseCard from '@/shared/components/JobBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
  onViewWorkflow?: (item: any) => void
  onDragStart?: (e: React.DragEvent) => void
}

export default function JobFailedCard({ item, onDelete, onProcess, onViewWorkflow, onDragStart }: Props) {
  return (
    <JobBaseCard
      item={item}
      dotColor="bg-red-500"
      statusText={
        <span className="text-red-500" title={item.error || 'Failed'}>
          <Warning className="w-1.5 h-1.5 inline mr-0.5" />
          {item.error ? item.error.slice(0, 50) : 'Failed'}
        </span>
      }
      onDelete={onDelete}
      onProcess={onProcess}
      onViewWorkflow={onViewWorkflow}
      onDragStart={onDragStart}
    />
  )
}
