import CompanyBaseCard from '@/shared/components/CompanyBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
}

export default function CompanyPendingCard({ item, onDelete, onProcess }: Props) {
  return (
    <CompanyBaseCard
      item={item}
      dotColor="bg-sky-400"
      statusText={<span className="text-sky-500">pending</span>}
      onDelete={onDelete}
      onProcess={onProcess}
    />
  )
}
