import CompanyBaseCard from '@/shared/components/CompanyBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onCancel?: () => void
  onReset?: () => void
}

export default function CompanyProcessingCard({ item, onDelete, onCancel, onReset }: Props) {
  const statusLabels: Record<string, string> = {
    starting: 'Starting', fetching: 'Fetching', analyzing: 'Analyzing',
    generating: 'Generating', finalizing: 'Finalizing',
  }
  const statusKey = statusLabels[item.status] || item.current_node || 'Processing'

  return (
    <CompanyBaseCard
      item={item}
      dotColor="bg-blue-500 animate-pulse"
      statusText={<span className="text-blue-500">{statusKey}...</span>}
      onDelete={onDelete}
      onCancel={onCancel}
      onReset={onReset}
    />
  )
}
