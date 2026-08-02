'use client'

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center h-screen gap-4 text-muted-foreground">
      <h2 className="text-lg font-semibold">Something went wrong</h2>
      <p className="text-sm">{error.message}</p>
      <button
        onClick={() => reset()}
        className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary/90"
      >
        Try again
      </button>
    </div>
  )
}
