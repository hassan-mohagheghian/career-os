import { Drawer, DrawerHeader, DrawerContent } from '@/shared/components/Drawer'
import AddJobForm from '@/features/jobs/components/AddJobForm'
import type { CreateJobRequest } from '@/features/jobs/hooks/useCreateJob'

interface AddJobDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (data: CreateJobRequest) => void
  submitting?: boolean
  error?: string | null
}

export default function AddJobDrawer({
  open,
  onOpenChange,
  onSubmit,
  submitting,
  error,
}: AddJobDrawerProps) {
  return (
    <Drawer open={open} onOpenChange={onOpenChange} variant="lg">
      <DrawerHeader title="Import Job" onClose={() => onOpenChange(false)} />
      <DrawerContent>
        <AddJobForm
          onSubmit={(data) => onSubmit(data)}
          onCancel={() => onOpenChange(false)}
          submitting={submitting}
          error={error || undefined}
        />
      </DrawerContent>
    </Drawer>
  )
}
