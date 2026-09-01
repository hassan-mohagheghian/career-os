import { useRef, useState, useEffect } from 'react'
import { CaretDown } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'

interface ClampTextProps {
  text: string
  className?: string
}

export function ClampText({ text, className }: ClampTextProps) {
  const ref = useRef<HTMLSpanElement>(null)
  const [truncated, setTruncated] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    setTruncated(el.scrollHeight > el.clientHeight + 1)
  }, [text])

  return (
    <span className={cn('relative group/clamp inline-flex items-start gap-0.5 min-w-0', className)}>
      <span ref={ref} className="line-clamp-2 leading-tight">
        {text}
      </span>
      {truncated && (
        <CaretDown className="w-3 h-3 shrink-0 text-muted-foreground/50 mt-0.5 group-hover/clamp:text-foreground transition-colors" />
      )}
    </span>
  )
}
