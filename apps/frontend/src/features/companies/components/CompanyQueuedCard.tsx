import CompanyBaseCard from '@/shared/components/CompanyBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
  onMoveToCreated?: () => void
}

export default function CompanyQueuedCard({ item, onDelete, onProcess, onMoveToCreated }: Props) {
  return (
    <CompanyBaseCard
      item={item}
      dotColor="bg-yellow-400"
      statusText={<span className="text-yellow-500">queued</span>}
      onDelete={onDelete}
      onProcess={onProcess}
      onMoveToCreated={onMoveToCreated}
    />
  )
}
