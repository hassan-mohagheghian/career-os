# Prompt 161 - A4 preview dialog for generated documents

## Objective

Add a **Preview** action to the generated Resume and Cover Letter cards in the
job application workspace that opens a dialog rendering the document content in
A4 page size (like a PDF), with the text fully selectable.

## Current state

`ApplicationDocuments.tsx` renders a `DocumentCard` per document
(`tailored_resume`, `cover_letter`). Existing actions: Copy, Download, Edit,
Delete, Generate/Regenerate. Content is shown only as a raw markdown `<pre>`
snippet; there is no full-page PDF-like preview.

## Implementation steps

1. Add `react-markdown` as a frontend dependency (safe markdown → HTML renderer;
   escapes raw HTML by default, so text is selectable DOM content).
2. New component `DocumentPreviewDialog.tsx`:
   - Props: `open`, `onOpenChange`, `label`, `content`.
   - Uses the shared `Dialog` (overridden to a wide, full-height layout).
   - Renders a **continuous A4-width** sheet (210mm wide, white paper, ~18-22mm
     margins, shadow). The height grows with the content instead of clipping at
     one fixed A4 box, so long resumes/cover letters read as one scrollable
     document top-to-bottom (PDF-like) and never look cluttered or cut off.
     The sheet lives in a scrollable dialog body.
   - Renders `content` with `ReactMarkdown` and a scoped stylesheet for PDF-like
     typography (headings, lists, blockquote, code, links).
   - Text is selectable (`user-select: text` on the sheet).
   - Responsive: below 640px the sheet fills the width instead of fixed A4.
3. Wire into `ApplicationDocuments.tsx`:
   - Add a Preview (`Eye`) icon button to each document card (only when a
     document exists).
   - Hold `previewOpen` state in `DocumentCard` and render
     `DocumentPreviewDialog` with the card's label + content.

## Testing requirements

- New `ApplicationDocuments.test.tsx`:
  - Preview button renders for an existing document; clicking it opens a dialog
    showing the document content (assert rendered markdown text is present).
  - No Preview button when the document does not exist.
  - Mock `@/entities/application/hooks` and `react-markdown` for the unit test.
- Run `cd apps/frontend && npx vitest run` (full suite) + `npm run typecheck`.

## Constraints

- Use the existing shared `Dialog` component; do not introduce a new modal
  primitive.
- Keep text selectable (regular DOM text via `ReactMarkdown`, not an image/PDF).
- Follow AGENTS.md: implementation-history first (this file), docs/tests before
  code; update `docs/ux/features/applications/application-documents.md`,
  `docs/ux/features/applications/workspace.md` and `docs/ux/DESIGN.md` with the
  Preview action and wireframe.
