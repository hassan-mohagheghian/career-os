import { useState } from 'react'
import { FileText, Repeat, Spinner } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import ResumePreview from '@/shared/components/ResumePreview'
import GenerationProgressCard from '@/shared/components/GenerationProgressCard'
import { TabHeader } from '@/shared/components/DrawerComponents'

const GENERATION_STEPS = [
  { key: 'prepare', label: 'Preparing' },
  { key: 'context', label: 'Load Context' },
  { key: 'generate', label: 'AI Generate' },
  { key: 'save', label: 'Save' },
  { key: 'done', label: 'Done' },
]

function DocumentSection({ title, content, isGenerating, generationProgress, hasContent, onGenerate, onCancel, emptyLabel }) {
  return (
    <div className="p-3 rounded-lg border border-primary/20 bg-primary/5">
      <div className="flex items-center justify-between mb-2">
        <TabHeader title={title} icon={<FileText className="w-3 h-3" />} className="font-semibold" />
        {!isGenerating && (
          <Button
            size="sm"
            onClick={onGenerate}
            className="gap-1.5 h-6 text-2xs bg-primary/15 text-primary hover:bg-primary/25 border border-primary/30"
          >
            <Repeat className="w-2.5 h-2.5" />
            {hasContent ? 'Regenerate' : 'Generate'}
          </Button>
        )}
      </div>

      {isGenerating && generationProgress && (
        <div className="mb-3">
          <GenerationProgressCard
            title={`Generating ${title}`}
            progress={generationProgress}
            steps={GENERATION_STEPS}
            onCancel={onCancel}
          />
        </div>
      )}

      {hasContent && !isGenerating ? (
        <div className="rounded-lg border border-primary/20 overflow-hidden bg-background">
          <ResumePreview html={content} />
        </div>
      ) : !isGenerating ? (
        <div className="flex flex-col items-center justify-center py-6 gap-2 rounded-lg border border-dashed border-primary/30 bg-background">
          <FileText className="w-6 h-6 text-primary/40" />
          <p className="text-2xs text-muted-foreground">{emptyLabel}</p>
        </div>
      ) : null}
    </div>
  )
}

export default function DocumentsTab({ job, resume, coverLetter, generationProgress, onGenerateResume, onGenerateCover, onCancelGeneration }) {
  const [activeDoc, setActiveDoc] = useState('resume')

  const isGeneratingResume = generationProgress?.running && generationProgress?.type === 'resume'
  const isGeneratingCover = generationProgress?.running && generationProgress?.type === 'cover'

  return (
    <div>
      <div className="flex gap-1 mb-3">
        <button
          onClick={() => setActiveDoc('resume')}
          className={cn(
            "px-3 py-1.5 rounded-md text-2xs font-semibold transition",
            activeDoc === 'resume'
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:text-foreground"
          )}
        >
          Resume {resume && <span className="ml-1 opacity-70">✓</span>}
        </button>
        <button
          onClick={() => setActiveDoc('cover')}
          className={cn(
            "px-3 py-1.5 rounded-md text-2xs font-semibold transition",
            activeDoc === 'cover'
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:text-foreground"
          )}
        >
          Cover Letter {coverLetter && <span className="ml-1 opacity-70">✓</span>}
        </button>
      </div>

      {activeDoc === 'resume' && (
        <DocumentSection
          title="Tailored Resume"
          content={resume?.content}
          isGenerating={isGeneratingResume}
          generationProgress={isGeneratingResume ? { ...generationProgress, type: 'resume' } : null}
          hasContent={!!resume}
          onGenerate={() => onGenerateResume(job.num)}
          onCancel={onCancelGeneration}
          emptyLabel="No resume generated yet"
        />
      )}

      {activeDoc === 'cover' && (
        <DocumentSection
          title="Cover Letter"
          content={coverLetter?.content}
          isGenerating={isGeneratingCover}
          generationProgress={isGeneratingCover ? { ...generationProgress, type: 'cover' } : null}
          hasContent={!!coverLetter}
          onGenerate={() => onGenerateCover(job.num)}
          onCancel={onCancelGeneration}
          emptyLabel="No cover letter generated yet"
        />
      )}
    </div>
  )
}
