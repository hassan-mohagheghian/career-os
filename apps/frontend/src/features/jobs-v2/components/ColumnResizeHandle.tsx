import { useCallback, useRef, type PointerEvent as ReactPointerEvent } from 'react'

interface ColumnResizeHandleProps {
  colIndex: number
  onResize: (colIndex: number, delta: number) => void
  onResizeStart: () => void
  onResizeEnd: () => void
}

export function ColumnResizeHandle({
  colIndex, onResize, onResizeStart, onResizeEnd,
}: ColumnResizeHandleProps) {
  const startX = useRef(0)

  const handlePointerDown = useCallback((e: ReactPointerEvent) => {
    e.preventDefault()
    e.stopPropagation()
    startX.current = e.clientX
    onResizeStart()

    const onPointerMove = (ev: PointerEvent) => {
      const delta = ev.clientX - startX.current
      startX.current = ev.clientX
      onResize(colIndex, delta)
    }

    const onPointerUp = () => {
      onResizeEnd()
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerup', onPointerUp)
    }

    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onPointerUp)
  }, [colIndex, onResize, onResizeStart, onResizeEnd])

  return (
    <div
      onPointerDown={handlePointerDown}
      className="absolute top-0 right-0 w-1.5 h-full cursor-col-resize group-hover/header:opacity-100 opacity-0 z-10"
      style={{ transform: 'translateX(50%)' }}
    >
      <div className="w-px h-full bg-border group-hover/header:bg-muted-foreground/40 transition-colors" />
    </div>
  )
}
