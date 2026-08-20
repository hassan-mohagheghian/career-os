'use client'

import { useState, useRef, type DragEvent, type ReactNode } from 'react'
import { extractUrlFromDataTransfer, dataTransferHasUrl } from '@/shared/lib/url-drag'
import { Plus } from '@phosphor-icons/react'

interface DropJobOverlayProps {
  /** Called with the dropped URL; opens the pre-filled Add Job drawer. */
  onDropUrl: (url: string) => void
  children: ReactNode
}

/**
 * Full-page drop surface for the Jobs page.
 *
 * Dragging a link from another browser tab into the app shows a "Drop to add
 * job" indicator; dropping anywhere on the page extracts the URL and hands it
 * to the parent, which opens the pre-filled Add Job drawer (the user then
 * chooses Add or Add & Queue). The dedicated Add Job button is its own drop
 * target with the same outcome.
 */
export function DropJobOverlay({ onDropUrl, children }: DropJobOverlayProps) {
  const [dragging, setDragging] = useState(false)
  const depthRef = useRef(0)

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    if (!dataTransferHasUrl(e.dataTransfer)) return
    depthRef.current += 1
    setDragging(true)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    if (!dataTransferHasUrl(e.dataTransfer)) return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    if (!dataTransferHasUrl(e.dataTransfer)) return
    depthRef.current = Math.max(0, depthRef.current - 1)
    if (depthRef.current === 0) setDragging(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    depthRef.current = 0
    setDragging(false)
    const url = extractUrlFromDataTransfer(e.dataTransfer)
    if (!url) return
    e.preventDefault()
    onDropUrl(url)
  }

  return (
    <div
      className="relative flex flex-col h-full"
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {children}
      {dragging && (
        <div className="pointer-events-none absolute inset-0 z-50 flex items-center justify-center bg-background/60">
          <div className="rounded-lg border-2 border-dashed border-emerald-500/60 bg-card px-6 py-4 flex items-center gap-2 text-sm font-medium text-foreground shadow-lg">
            <Plus className="w-4 h-4 text-emerald-500" />
            Drop to add job
          </div>
        </div>
      )}
    </div>
  )
}