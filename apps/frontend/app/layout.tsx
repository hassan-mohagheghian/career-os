import type { Metadata } from 'next'
import { Providers } from '@/app/providers'
import './globals.css'

export const metadata: Metadata = {
  title: 'Job Search Intelligence',
  description: 'AI-powered career platform for software engineers',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
