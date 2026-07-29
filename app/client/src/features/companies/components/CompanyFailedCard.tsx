import { Warning } from '@phosphor-icons/react'
import CompanyBaseCard from '@/shared/components/CompanyBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onProcess?: () => void
}

export default function CompanyFailedCard({ item, onDelete, onProcess }: Props) {
  return (
    <CompanyBaseCard
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
    />
  )
}
