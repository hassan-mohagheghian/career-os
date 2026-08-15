'use client'

import ReactMarkdown from 'react-markdown'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/shared/ui/dialog'

interface DocumentPreviewDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  label: string
  content: string
}

// A4-width continuous sheet: 210mm wide, height grows with content so it
// scrolls as one long page (like a multi-page PDF laid out top to bottom).
const SHEET_STYLE = `
  .doc-preview-a4 {
    width: 210mm;
    min-height: 297mm;
    height: auto;
    background: #ffffff;
    color: #171717;
    padding: 18mm 22mm 24mm;
    box-shadow: 0 8px 30px rgb(0 0 0 / 0.25);
    font-size: 13px;
    line-height: 1.7;
    user-select: text;
    -webkit-user-select: text;
    box-sizing: border-box;
  }
  .doc-preview-a4 * { box-sizing: border-box; }
  .doc-preview-a4 h1 { font-size: 24px; font-weight: 700; margin: 0 0 6px; line-height: 1.25; }
  .doc-preview-a4 h2 { font-size: 16px; font-weight: 700; margin: 22px 0 8px; line-height: 1.3; }
  .doc-preview-a4 h3 { font-size: 14px; font-weight: 600; margin: 16px 0 6px; }
  .doc-preview-a4 p { margin: 7px 0; }
  .doc-preview-a4 ul, .doc-preview-a4 ol { margin: 7px 0; padding-left: 22px; }
  .doc-preview-a4 li { margin: 4px 0; }
  .doc-preview-a4 hr { margin: 20px 0; border: 0; border-top: 1px solid #d4d4d4; }
  .doc-preview-a4 strong { font-weight: 600; }
  .doc-preview-a4 blockquote { margin: 10px 0; padding-left: 14px; border-left: 3px solid #d4d4d4; color: #404040; }
  .doc-preview-a4 code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.9em; }
  .doc-preview-a4 pre { background: #f5f5f5; padding: 10px 12px; border-radius: 6px; overflow-x: auto; margin: 10px 0; }
  .doc-preview-a4 pre code { background: transparent; padding: 0; }
  .doc-preview-a4 a { color: #2563eb; text-decoration: underline; }
  @media (max-width: 640px) {
    .doc-preview-a4 { width: 100%; min-height: auto; padding: 12mm 14mm; }
  }
`

export function DocumentPreviewDialog({ open, onOpenChange, label, content }: DocumentPreviewDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="w-[min(94vw,230mm)] max-w-none gap-0 p-0 sm:max-w-none overflow-hidden"
      >
        <style>{SHEET_STYLE}</style>
        <DialogHeader className="px-4 py-3 border-b border-border/60 bg-muted/10 shrink-0">
          <DialogTitle>{label} — Preview</DialogTitle>
          <DialogDescription>
            A4-width preview · text is selectable
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto max-h-[80vh] bg-muted/40 p-4 flex justify-center items-start">
          <div className="doc-preview-a4 shrink-0">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
