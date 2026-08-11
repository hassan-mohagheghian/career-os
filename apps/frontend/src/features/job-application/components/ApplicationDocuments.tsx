'use client'

import { useState } from 'react'
import {
  CircleNotch,
  Copy,
  Download,
  FileText,
  NotePencil,
  PencilSimple,
  Trash,
  Check,
  X,
} from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import { Textarea } from '@/shared/ui/textarea'
import DateTime from '@/shared/components/DateTime'
import type { ApplicationDetail, ApplicationDocument, ApplicationDocumentType } from '@/entities/application/types'
import {
  useDeleteDocumentMutation,
  useGenerateDocumentMutation,
  useUpdateDocumentMutation,
} from '@/entities/application/hooks'

interface ApplicationDocumentsProps {
  application: ApplicationDetail
  generatingType: ApplicationDocumentType | null
  onGenerate: (documentType: ApplicationDocumentType) => void
}

const documentLabels: Record<ApplicationDocumentType, string> = {
  tailored_resume: 'Tailored Resume',
  cover_letter: 'Cover Letter',
}

function useCopyToClipboard() {
  const [copied, setCopied] = useState(false)
  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // clipboard unavailable
    }
  }
  return { copied, copy }
}

function DocumentCard({
  doc,
  documentType,
  onGenerate,
  generating,
}: {
  doc: ApplicationDocument | null
  documentType: ApplicationDocumentType
  onGenerate: () => void
  generating: boolean
}) {
  const type = doc?.document_type ?? documentType
  const label = documentLabels[type]
  const updateDocument = useUpdateDocumentMutation()
  const deleteDocument = useDeleteDocumentMutation()
  const { copied, copy } = useCopyToClipboard()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(doc?.content ?? '')

  const handleDownload = () => {
    const blob = new Blob([doc?.content ?? ''], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${label.replace(/\s+/g, '-').toLowerCase()}-v${doc?.version ?? 1}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleSave = () => {
    if (!doc) return
    updateDocument.mutate({ documentId: doc.id, content: draft })
    setEditing(false)
  }

  return (
    <div className="rounded-lg border border-border/40 bg-muted/10 p-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-4 h-4 text-primary shrink-0" />
          <p className="text-xs font-medium text-foreground truncate">{label}</p>
          {doc && (
            <span className="text-2xs text-muted-foreground shrink-0">v{doc.version}</span>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {doc ? (
            <>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0" aria-label="Copy content" onClick={() => copy(doc.content)}>
                {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
              </Button>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0" aria-label="Download" onClick={handleDownload}>
                <Download className="w-3.5 h-3.5" />
              </Button>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0" aria-label="Edit content" onClick={() => { setDraft(doc.content); setEditing(true) }}>
                <PencilSimple className="w-3.5 h-3.5" />
              </Button>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0" aria-label="Delete document" onClick={() => deleteDocument.mutate(doc.id)}>
                <Trash className="w-3.5 h-3.5 text-red-500" />
              </Button>
            </>
          ) : null}
          <Button variant="outline" size="sm" className="h-7 gap-1 text-xs" onClick={onGenerate} disabled={generating}>
            {generating ? <CircleNotch className="w-3.5 h-3.5 animate-spin" /> : <NotePencil className="w-3.5 h-3.5" />}
            {doc ? 'Regenerate' : 'Generate'}
          </Button>
        </div>
      </div>

      {!doc && !generating && (
        <p className="text-xs text-muted-foreground">
          No {label.toLowerCase()} yet. Generate one from the job analysis and your profile.
        </p>
      )}
      {generating && !doc && (
        <p className="text-xs text-muted-foreground">Generating {label.toLowerCase()}…</p>
      )}

      {doc && editing && (
        <div className="space-y-2">
          <Textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="min-h-40 text-xs font-mono"
          />
          <div className="flex items-center gap-2 justify-end">
            <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={() => setEditing(false)}>
              <X className="w-3.5 h-3.5 mr-1" /> Cancel
            </Button>
            <Button variant="outline" size="sm" className="h-6 text-xs" onClick={handleSave} disabled={updateDocument.isPending}>
              <Check className="w-3.5 h-3.5 mr-1" /> Save
            </Button>
          </div>
        </div>
      )}

      {doc && !editing && (
        <div className="max-h-48 overflow-y-auto rounded bg-background/60 border border-border/40 p-2">
          <pre className="text-2xs text-foreground whitespace-pre-wrap font-mono">
            {doc.content || '(empty)'}
          </pre>
        </div>
      )}

      {doc && !editing && (
        <p className="text-2xs text-muted-foreground">
          Updated <DateTime value={doc.updated_at} />
        </p>
      )}
    </div>
  )
}

export function ApplicationDocuments({ application, generatingType, onGenerate }: ApplicationDocumentsProps) {
  const resume = application.documents.find((d) => d.document_type === 'tailored_resume') ?? null
  const coverLetter = application.documents.find((d) => d.document_type === 'cover_letter') ?? null

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
      <DocumentCard
        doc={resume}
        documentType="tailored_resume"
        generating={generatingType === 'tailored_resume'}
        onGenerate={() => onGenerate('tailored_resume')}
      />
      <DocumentCard
        doc={coverLetter}
        documentType="cover_letter"
        generating={generatingType === 'cover_letter'}
        onGenerate={() => onGenerate('cover_letter')}
      />
    </div>
  )
}
