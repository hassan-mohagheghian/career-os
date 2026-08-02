import CompanyBaseCard from '@/shared/components/CompanyBaseCard'

interface Props {
  item: any
  onCancel?: () => void
}

export default function CompanyProcessingCard({ item, onCancel }: Props) {
  const statusKey = item.current_node || 'Processing'

  return (
    <CompanyBaseCard
      item={item}
      dotColor="bg-blue-500 animate-pulse"
      statusText={<span className="text-blue-500">Processing...</span>}
      onCancel={onCancel}
    />
  )
}
