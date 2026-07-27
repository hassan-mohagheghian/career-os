import { useState, useEffect } from 'react'
import { FileText, Repeat, X, Spinner } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import ResumePreview from '@/shared/components/ResumePreview'
import GenerationProgressCard from '@/shared/components/GenerationProgressCard'
import GenerationHistoryItem from '@/shared/components/GenerationHistoryItem'
import { TabHeader } from '@/shared/components/DrawerComponents'
import { useLocalHistory } from '@/shared/hooks'
import { STEP_CONFIGS } from '@/shared/components/GenerationProgressCard'

export default function DocumentsTab({ job, resume, coverLetter, activeGens, onGenerateResume, onGenerateCover, onCancelGeneration }) {
  const [activeDoc, setActiveDoc] = useState('resume')
  const { items: localHistory, refresh } = useLocalHistory({
    context: 'job',
    job_num: job.num,
  })

  const resumeGen = activeGens?.resume || null
  const coverGen = activeGens?.cover || null

  const resumeHistory = localHistory.filter(h => h.source === 'generation' && (h as any).type === 'resume')
  const coverHistory = localHistory.filter(h => h.source === 'generation' && ((h as any).type === 'cover' || (h as any).type === 'cover_letter'))

  const hasResume = !!resume
  const hasCover = !!coverLetter
  const resumeRunning = resumeGen?.running
  const coverRunning = coverGen?.running

  // Refresh local history when active gens change
  useEffect(() => {
    refresh()
  }, [activeGens, refresh])

  return (
    <div>
      {/* Resume / Cover toggle */}
      <Tabs value={activeDoc} onValueChange={setActiveDoc} className="mb-3">
        <TabsList className="bg-muted">
          <TabsTrigger value="resume">Resume{hasResume && ' ✓'}</TabsTrigger>
          <TabsTrigger value="cover">Cover Letter{hasCover && ' ✓'}</TabsTrigger>
        </TabsList>
      </Tabs>

      {activeDoc === 'resume' && (
        <div className="space-y-3">
          <div className="p-3 rounded-lg border border-primary/20 bg-primary/5">
            <div className="flex items-center justify-between mb-2">
              <TabHeader title="Tailored Resume" icon={<FileText className="w-3 h-3" />} className="font-semibold" />
              {resumeRunning ? (
                <Button
                  size="sm"
                  onClick={() => onCancelGeneration('resume')}
                  className="gap-1.5 h-6 text-2xs bg-destructive/15 text-destructive hover:bg-destructive/25 border border-destructive/30"
                >
                  <X className="w-2.5 h-2.5" />
                  Cancel
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={() => onGenerateResume(job.num)}
                  className="gap-1.5 h-6 text-2xs bg-primary/15 text-primary hover:bg-primary/25 border border-primary/30"
                >
                  <Repeat className="w-2.5 h-2.5" />
                  {hasResume ? 'Regenerate' : 'Generate'}
                </Button>
              )}
            </div>
            {hasResume && !resumeGen ? (
              <div className="rounded-lg border border-primary/20 overflow-hidden bg-background">
                <ResumePreview html={resume.content} />
              </div>
            ) : !resumeGen ? (
              <div className="flex flex-col items-center justify-center py-6 gap-2 rounded-lg border border-dashed border-primary/30 bg-background">
                <FileText className="w-6 h-6 text-primary/40" />
                <p className="text-2xs text-muted-foreground">No resume generated yet</p>
              </div>
            ) : null}
          </div>
          {/* Resume history */}
          {resumeGen && (
            <div className="rounded-lg border border-primary/20 bg-primary/5 p-2">
              <GenerationProgressCard
                title={`Generating Resume`}
                progress={resumeGen}
                steps={STEP_CONFIGS['resume']?.steps}
                onCancel={() => onCancelGeneration('resume')}
              />
            </div>
          )}
          <div className="space-y-0.5">
            <p className="text-2xs font-semibold text-muted-foreground">History</p>
            {resumeHistory.map(h => (
              <GenerationHistoryItem key={`${h.source}-${h.id}`} item={h} compact />
            ))}
            {resumeHistory.length === 0 && !resumeGen && (
              <p className="text-2xs text-muted-foreground py-2 text-center">No generation history yet</p>
            )}
          </div>
        </div>
      )}

      {activeDoc === 'cover' && (
        <div className="space-y-3">
          <div className="p-3 rounded-lg border border-primary/20 bg-primary/5">
            <div className="flex items-center justify-between mb-2">
              <TabHeader title="Cover Letter" icon={<FileText className="w-3 h-3" />} className="font-semibold" />
              {coverRunning ? (
                <Button
                  size="sm"
                  onClick={() => onCancelGeneration('cover')}
                  className="gap-1.5 h-6 text-2xs bg-destructive/15 text-destructive hover:bg-destructive/25 border border-destructive/30"
                >
                  <X className="w-2.5 h-2.5" />
                  Cancel
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={() => onGenerateCover(job.num)}
                  className="gap-1.5 h-6 text-2xs bg-primary/15 text-primary hover:bg-primary/25 border border-primary/30"
                >
                  <Repeat className="w-2.5 h-2.5" />
                  {hasCover ? 'Regenerate' : 'Generate'}
                </Button>
              )}
            </div>
            {hasCover && !coverGen ? (
              <div className="rounded-lg border border-primary/20 overflow-hidden bg-background">
                <ResumePreview html={coverLetter.content} />
              </div>
            ) : !coverGen ? (
              <div className="flex flex-col items-center justify-center py-6 gap-2 rounded-lg border border-dashed border-primary/30 bg-background">
                <FileText className="w-6 h-6 text-primary/40" />
                <p className="text-2xs text-muted-foreground">No cover letter generated yet</p>
              </div>
            ) : null}
          </div>
          {/* Cover letter history */}
          {coverGen && (
            <div className="rounded-lg border border-primary/20 bg-primary/5 p-2">
              <GenerationProgressCard
                title={`Generating Cover Letter`}
                progress={coverGen}
                steps={STEP_CONFIGS['cover-letter']?.steps}
                onCancel={() => onCancelGeneration('cover')}
              />
            </div>
          )}
          <div className="space-y-0.5">
            <p className="text-2xs font-semibold text-muted-foreground">History</p>
            {coverHistory.map(h => (
              <GenerationHistoryItem key={`${h.source}-${h.id}`} item={h} compact />
            ))}
            {coverHistory.length === 0 && !coverGen && (
              <p className="text-2xs text-muted-foreground py-2 text-center">No generation history yet</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
