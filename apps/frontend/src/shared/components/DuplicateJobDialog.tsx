import { TrendUp, Repeat, Warning } from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/shared/ui/dialog'

export default function DuplicateJobDialog({ duplicateJob, setDuplicateJob, onRescore, onReprocess }) {
  if (!duplicateJob) return null

  return (
    <Dialog open={!!duplicateJob} onOpenChange={(open) => !open && setDuplicateJob(null)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Warning className="w-5 h-5 text-yellow-500" />
            Job Already Exists
          </DialogTitle>
          <DialogDescription>How would you like to update this job?</DialogDescription>
        </DialogHeader>
        <Card className="p-3 bg-muted">
          <div className="text-sm font-bold">{duplicateJob?.id} {duplicateJob?.company}</div>
          <div className="text-xs mt-1 text-muted-foreground">
            Score: <span className="font-bold" style={{ color: ['A','A+','A++'].includes(duplicateJob?.score) ? '#22c55e' : ['B','C'].includes(duplicateJob?.score) ? '#eab308' : '#ef4444' }}>{duplicateJob?.score}</span>
            {' · '}
            Match: <span className="font-bold text-primary">{duplicateJob?.match}</span>
          </div>
        </Card>
        <DialogFooter className="flex-row gap-2">
          <Button className="flex-1 gap-1" onClick={() => onRescore(duplicateJob.id)}>
            <TrendUp className="w-3.5 h-3.5" /> Rescore
          </Button>
          <Button variant="outline" className="flex-1 gap-1" onClick={() => onReprocess(duplicateJob.id)}>
            <Repeat className="w-3.5 h-3.5" /> Reprocess
          </Button>
          <Button variant="ghost" onClick={() => setDuplicateJob(null)}>Cancel</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
