'use client'

import { useEffect, useRef, useState } from 'react'
import { LinkSimple, Copy, Check } from '@phosphor-icons/react'
import { cn } from '@/shared/lib/utils'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip'
import { COPY_FEEDBACK_TIMEOUT } from '@/shared/config/constants'

export function normalizeLinkUrl(url: string): string {
  const trimmed = url.trim()
  if (/^(https?:\/\/|mailto:)/i.test(trimmed)) return trimmed
  return `https://${trimmed}`
}

export function isSafeLink(url: string): boolean {
  return /^(https?:\/\/|mailto:)/i.test(url.trim())
}

export function truncateLink(url: string, maxLength = 50): string {
  const clean = url.replace(/^https?:\/\//i, '').replace(/^www\./i, '')
  if (clean.length <= maxLength) return clean
  return `${clean.slice(0, maxLength)}...`
}

async function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  const el = document.createElement('textarea')
  el.value = text
  el.style.position = 'fixed'
  el.style.opacity = '0'
  document.body.appendChild(el)
  el.select()
  document.execCommand('copy')
  document.body.removeChild(el)
}

interface LinkDisplayProps {
  url: string
  title?: string | null
  maxLength?: number
  className?: string
  hideIcon?: boolean
  copyLabel?: string
  openLabel?: string
}

export default function LinkDisplay({
  url,
  title,
  maxLength = 50,
  className,
  hideIcon = false,
  copyLabel = 'Copy link',
  openLabel = 'Open link',
}: LinkDisplayProps) {
  const [copied, setCopied] = useState(false)
  const timeoutRef = useRef<number | null>(null)

  const safe = isSafeLink(url)
  const href = normalizeLinkUrl(url)
  const display = title?.trim() || truncateLink(url, maxLength)

  useEffect(() => () => {
    if (timeoutRef.current) window.clearTimeout(timeoutRef.current)
  }, [])

  const handleCopy = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      await copyToClipboard(url)
      setCopied(true)
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current)
      timeoutRef.current = window.setTimeout(() => setCopied(false), COPY_FEEDBACK_TIMEOUT)
    } catch {
      // best effort
    }
  }

  return (
    <div className={cn('group flex min-w-0 items-center gap-1', className)}>
      <Tooltip>
        <TooltipTrigger asChild>
          {safe ? (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={title || openLabel}
              className="flex min-w-0 flex-1 items-center gap-1 text-primary hover:underline"
            >
              {!hideIcon && <LinkSimple className="h-3 w-3 shrink-0" weight="bold" />}
              <span className="min-w-0 truncate">{display}</span>
            </a>
          ) : (
            <span
              aria-label={url}
              className="flex min-w-0 flex-1 items-center gap-1 text-muted-foreground"
            >
              {!hideIcon && <LinkSimple className="h-3 w-3 shrink-0" weight="bold" />}
              <span className="min-w-0 truncate">{display}</span>
            </span>
          )}
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-[320px] text-xs">
          <span className="break-all">{url}</span>
        </TooltipContent>
      </Tooltip>
      <button
        type="button"
        onClick={handleCopy}
        aria-label={copied ? 'Copied' : copyLabel}
        title={copied ? 'Copied' : copyLabel}
        className="shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:bg-muted hover:text-foreground focus:opacity-100 group-hover:opacity-100"
      >
        {copied ? <Check className="h-3 w-3 text-emerald-500" weight="bold" /> : <Copy className="h-3 w-3" />}
      </button>
    </div>
  )
}
