import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-screen gap-4 text-muted-foreground">
      <h2 className="text-lg font-semibold">Page Not Found</h2>
      <p className="text-sm">The page you are looking for does not exist.</p>
      <Link
        href="/jobs"
        className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary/90"
      >
        Go to Jobs
      </Link>
    </div>
  )
}
