import { cn } from '@/lib/utils'

export function Section({ title, icon, children }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-[0.6rem] uppercase tracking-wider mb-1 text-primary">
        {icon}{title}
      </div>
      {children}
    </div>
  )
}

export function TabHeader({ title, icon, className }) {
  return (
    <h4 className={cn("text-[0.6rem] uppercase tracking-wider mb-1 text-primary", className)}>
      {icon && <span className="inline-flex items-center gap-1.5">{icon}</span>}
      {title}
    </h4>
  )
}

export function Field({ label, value }) {
  if (!value) return null
  return (
    <div className="flex gap-2">
      <span className="text-sm text-muted-foreground shrink-0">{label}:</span>
      <span className="text-sm">{value}</span>
    </div>
  )
}

export function TagList({ items }) {
  if (!items || !items.length) return null
  return (
    <div className="flex flex-wrap gap-1">
      {items.map((item, i) => (
        <span key={i} className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold bg-secondary text-secondary-foreground">
          {item}
        </span>
      ))}
    </div>
  )
}

export function ScoreBadge({ value, label, size = 'lg', color = 'primary' }) {
  const sizeClasses = {
    '4xl': 'text-4xl font-black',
    '3xl': 'text-3xl font-black',
    'lg': 'text-lg font-bold',
  }
  const colorClasses = {
    primary: 'text-primary',
    blue: 'text-blue-400',
    emerald: 'text-emerald-400',
    purple: 'text-purple-400',
  }
  return (
    <div className="flex flex-col items-center">
      <div className={cn(sizeClasses[size], colorClasses[color])}>{value ?? '?'}</div>
      <div className="text-[0.5rem] uppercase tracking-wider text-muted-foreground font-semibold">{label}</div>
    </div>
  )
}
