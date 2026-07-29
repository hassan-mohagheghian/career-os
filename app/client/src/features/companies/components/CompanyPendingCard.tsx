import CompanyBaseCard from '@/shared/components/CompanyBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
  onReset?: () => void
}

export default function CompanyPendingCard({ item, onDelete, onProcess, onReset }: Props) {
  return (
    <CompanyBaseCard
      item={item}
      dotColor="bg-muted-foreground"
      statusText={<span className="text-gray-400">created</span>}
      onDelete={onDelete}
      onProcess={onProcess}
      onReset={onReset}
    />
  )
}
