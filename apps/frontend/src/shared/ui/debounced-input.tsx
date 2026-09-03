'use client'

import * as React from 'react'
import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/lib/utils'
import { DEBOUNCE_DELAY } from '@/shared/config/constants'

export interface DebouncedInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange' | 'defaultValue'> {
  value: string
  onValueChange: (value: string) => void
  debounceMs?: number
  icon?: React.ReactNode
  clearable?: boolean
  clearLabel?: string
  activeClassName?: string
  wrapperClassName?: string
  inputClassName?: string
  ref?: React.Ref<HTMLInputElement>
}

export function DebouncedInput({
  value,
  onValueChange,
  debounceMs = DEBOUNCE_DELAY,
  icon,
  clearable = false,
  clearLabel = 'Clear input',
  activeClassName,
  wrapperClassName,
  inputClassName,
  className,
  type,
  ref,
  'aria-label': ariaLabel,
  ...rest
}: DebouncedInputProps) {
  const [localValue, setLocalValue] = React.useState(value)
  const timerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)
  const localValueRef = React.useRef(value)

  const clearTimer = React.useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  React.useEffect(() => () => clearTimer(), [clearTimer])

  React.useEffect(() => {
    if (value !== localValueRef.current) {
      clearTimer()
      localValueRef.current = value
      setLocalValue(value)
    }
  }, [value, clearTimer])

  const handleChange = React.useCallback((next: string) => {
    setLocalValue(next)
    localValueRef.current = next
    clearTimer()
    if (next === '') {
      onValueChange('')
      return
    }
    timerRef.current = setTimeout(() => onValueChange(next), debounceMs)
  }, [clearTimer, debounceMs, onValueChange])

  const handleClear = React.useCallback(() => {
    setLocalValue('')
    localValueRef.current = ''
    clearTimer()
    onValueChange('')
  }, [clearTimer, onValueChange])

  const handleKeyDown = React.useCallback((event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape' && localValueRef.current) {
      event.preventDefault()
      handleClear()
    }
  }, [handleClear])

  return (
    <div className={cn('relative', wrapperClassName, className)}>
      {icon && (
        <span className="pointer-events-none absolute left-2 top-1/2 -translate-y-1/2 flex items-center text-muted-foreground">
          {icon}
        </span>
      )}
      <Input
        ref={ref}
        type={type ?? 'text'}
        value={localValue}
        onChange={(e) => handleChange(e.target.value)}
        onKeyDown={handleKeyDown}
        aria-label={ariaLabel}
        className={cn(inputClassName, localValue !== '' && activeClassName)}
        {...rest}
      />
      {clearable && localValue !== '' && (
        <button
          type="button"
          onClick={handleClear}
          aria-label={clearLabel}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-2xs text-muted-foreground hover:text-foreground"
        >
          ✕
        </button>
      )}
    </div>
  )
}

export default DebouncedInput
