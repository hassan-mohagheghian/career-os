import CompanyBaseCard from '@/shared/components/CompanyBaseCard'

interface Props {
  item: any
  onDelete?: () => void
  onCancel?: () => void
  onReset?: () => void
}

export default function CompanyProcessingCard({ item, onDelete, onCancel, onReset }: Props) {
  const statusKey = (() => {
    const labels = ['Fetching', 'Extracting', 'Analyzing', 'Saving', 'Done']
    const vals = ['step_fetch', 'step_extract', 'step_analyze', 'step_save', 'step_done'].map(k => item[k])
    const done = vals.filter((s: number) => s === 1).length
    return labels[Math.min(done, labels.length - 1)] || 'Processing'
  })()

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
