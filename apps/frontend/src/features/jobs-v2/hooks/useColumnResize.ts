import { useState, useCallback, useEffect, useRef } from 'react'

const STORAGE_KEY = 'jobs-table-column-widths'
const MIN_COL_WIDTH = 50
const MIN_LEADING_WIDTH = 44

function parseGridTemplate(template: string): number[] {
  return template.split(/\s+/).map(part => {
    const match = part.match(/^(\d+)px/)
    return match ? parseInt(match[1], 10) : 100
  })
}

function buildGridTemplate(widths: number[]): string {
  return widths.map(w => `${Math.round(w)}px`).join(' ')
}

export function useColumnResize(defaultTemplate: string) {
  const [widths, setWidths] = useState<number[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) return parsed
      }
    } catch { /* ignore */ }
    return parseGridTemplate(defaultTemplate)
  })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(widths))
  }, [widths])

  const onResize = useCallback((colIndex: number, delta: number) => {
    setWidths(prev => {
      const next = [...prev]
      const minWidth = colIndex < 2 ? MIN_LEADING_WIDTH : MIN_COL_WIDTH
      next[colIndex] = Math.max(minWidth, next[colIndex] + delta)
      return next
    })
  }, [])

  const onResizeStart = useCallback(() => {
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [])

  const onResizeEnd = useCallback(() => {
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }, [])

  const reset = useCallback(() => {
    setWidths(parseGridTemplate(defaultTemplate))
  }, [defaultTemplate])

  return {
    gridTemplate: buildGridTemplate(widths),
    onResize,
    onResizeStart,
    onResizeEnd,
    reset,
    columnCount: widths.length,
  }
}
