import { cn } from '@/shared/lib/utils'

export function PageHeader({
  title,
  children,
  className,
}: {
  title: string
  children?: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn("flex items-center justify-between shrink-0", className)}>
      <h1 className="text-xl font-bold tracking-tight">{title}</h1>
      {children && (
        <div className="flex items-center gap-2">
          {children}
        </div>
      )}
    </div>
  )
}
