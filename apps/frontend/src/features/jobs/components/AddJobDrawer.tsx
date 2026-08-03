'use client'

import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
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
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[480px] p-0 flex flex-col h-full">
        <SheetHeader className="shrink-0 flex flex-row items-center justify-between px-4 py-3 border-b border-border/40">
          <SheetTitle className="text-sm font-semibold">Import Job</SheetTitle>
        </SheetHeader>
        <div className="flex-1 min-h-0">
          <AddJobForm
            onSubmit={(data) => onSubmit(data)}
            onCancel={() => onOpenChange(false)}
            submitting={submitting}
            error={error || undefined}
          />
        </div>
      </SheetContent>
    </Sheet>
  )
}
