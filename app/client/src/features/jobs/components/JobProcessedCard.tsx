import JobBaseCard from '@/shared/components/JobBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
  onViewWorkflow?: (item: any) => void
}

export default function JobProcessedCard({ item, onDelete, onProcess, onViewWorkflow }: Props) {
  return (
    <JobBaseCard
      item={item}
      dotColor="bg-green-500"
      statusText={<span className="text-green-500">processed</span>}
      onDelete={onDelete}
      onProcess={onProcess}
      onViewWorkflow={onViewWorkflow}
    />
  )
}
