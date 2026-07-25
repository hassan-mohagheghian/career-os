import { useState } from 'react'
import { FileText, Repeat, Spinner } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Button } from '@/shared/ui/button'
import ResumePreview from '@/shared/components/ResumePreview'
import { TabHeader } from '@/shared/components/DrawerComponents'

function DocumentSection({ title, content, isGenerating, hasContent, onGenerate, emptyLabel }) {
  return (
    <div className="p-3 rounded-lg border border-primary/20 bg-primary/5">
      <div className="flex items-center justify-between mb-2">
        <TabHeader title={title} icon={<FileText className="w-3 h-3" />} className="font-semibold" />
        <Button
          size="sm"
          onClick={onGenerate}
          disabled={isGenerating}
          className="gap-1.5 h-6 text-[0.55rem] bg-primary/15 text-primary hover:bg-primary/25 border border-primary/30"
        >
          {isGenerating ? <Spinner className="w-2.5 h-2.5 animate-spin" /> : <Repeat className="w-2.5 h-2.5" />}
          {isGenerating ? 'Generating...' : hasContent ? 'Regenerate' : 'Generate'}
        </Button>
      </div>
      {hasContent ? (
        <div className="rounded-lg border border-primary/20 overflow-hidden bg-background">
          <ResumePreview html={content} />
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-6 gap-2 rounded-lg border border-dashed border-primary/30 bg-background">
          <FileText className="w-6 h-6 text-primary/40" />
          <p className="text-[0.6rem] text-muted-foreground">{emptyLabel}</p>
        </div>
      )}
    </div>
  )
}

export default function DocumentsTab({ job, resume, coverLetter, generatingResume, generatingCover, onGenerateResume, onGenerateCover }) {
  const [activeDoc, setActiveDoc] = useState('resume')

  return (
    <div>
      <div className="flex gap-1 mb-3">
        <button
          onClick={() => setActiveDoc('resume')}
          className={cn(
            "px-3 py-1.5 rounded-md text-[0.6rem] font-semibold transition",
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
            "px-3 py-1.5 rounded-md text-[0.6rem] font-semibold transition",
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
          isGenerating={generatingResume}
          hasContent={!!resume}
          onGenerate={() => onGenerateResume(job.num)}
          emptyLabel="No resume generated yet"
        />
      )}

      {activeDoc === 'cover' && (
        <DocumentSection
          title="Cover Letter"
          content={coverLetter?.content}
          isGenerating={generatingCover}
          hasContent={!!coverLetter}
          onGenerate={() => onGenerateCover(job.num)}
          emptyLabel="No cover letter generated yet"
        />
      )}
    </div>
  )
}
