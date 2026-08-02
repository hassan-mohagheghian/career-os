import CompanyBaseCard from '@/shared/components/CompanyBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
}

export default function CompanyCreatedCard({ item, onDelete, onProcess }: Props) {
  return (
    <CompanyBaseCard
      item={item}
      dotColor="bg-muted-foreground"
      statusText={<span className="text-gray-400">created</span>}
      onDelete={onDelete}
      onProcess={onProcess}
    />
  )
}
