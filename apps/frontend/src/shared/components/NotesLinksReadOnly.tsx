import { Note, LinkSimple } from '@phosphor-icons/react'

export interface ReadOnlyNote {
  id?: string | number
  title?: string | null
  content?: string
}

export interface ReadOnlyLink {
  id?: string | number
  url?: string | null
  title?: string | null
  description?: string | null
}

interface NotesLinksReadOnlyProps {
  notes?: ReadOnlyNote[]
  links?: ReadOnlyLink[]
  heading?: string
}

export default function NotesLinksReadOnly({ notes = [], links = [], heading = 'Notes & Links' }: NotesLinksReadOnlyProps) {
  const visibleNotes = notes.filter((n) => !!n.content)
  const visibleLinks = links.filter((l) => !!l.url)

  if (visibleNotes.length === 0 && visibleLinks.length === 0) return null

  return (
    <div className="rounded-lg border border-border/40 bg-muted/10 p-3 space-y-3">
      <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wide">{heading}</p>
      {visibleNotes.length > 0 && (
        <div className="space-y-1.5">
          {visibleNotes.map((n, i) => (
            <div key={n.id ?? i} className="flex items-start gap-1.5 text-xs text-foreground">
              <Note className="w-3 h-3 text-muted-foreground mt-0.5 shrink-0" />
              <span className="min-w-0 whitespace-pre-wrap break-words">
                {n.title && <span className="font-medium">{n.title}: </span>}
                {n.content}
              </span>
            </div>
          ))}
        </div>
      )}
      {visibleLinks.length > 0 && (
        <div className="space-y-1.5">
          {visibleLinks.map((l, i) => (
            <a
              key={l.id ?? i}
              href={l.url ?? '#'}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-xs text-primary hover:underline break-all"
            >
              <LinkSimple className="w-3 h-3 text-muted-foreground shrink-0" />
              <span className="min-w-0 break-all">{l.title || l.url}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}
