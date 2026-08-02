import CompanyBaseCard from '@/shared/components/CompanyBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
}

export default function CompanyProcessedCard({ item, onDelete, onProcess }: Props) {
  return (
    <CompanyBaseCard
      item={item}
      dotColor="bg-green-500"
      statusText={<span className="text-green-500">processed</span>}
      onDelete={onDelete}
      onProcess={onProcess}
    />
  )
}
