'use client'

import Link from 'next/link'

export function LegacyBanner() {
  return (
    <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2">
      <p className="text-xs text-amber-600 dark:text-amber-400 text-center">
        ⚠️ This is the <strong>Legacy Jobs List</strong>. It has been replaced by the{' '}
        <Link href="/jobs" className="underline hover:no-underline font-medium">new Jobs list</Link>.
      </p>
    </div>
  )
}
