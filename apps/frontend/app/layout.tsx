import type { Metadata } from 'next'
import { Providers } from '@/app/providers'
import './globals.css'
import { JetBrains_Mono, Merriweather } from "next/font/google";
import { cn } from "@/shared/lib/utils";

const merriweatherHeading = Merriweather({subsets:['latin'],variable:'--font-heading'});

const jetbrainsMono = JetBrains_Mono({subsets:['latin'],variable:'--font-mono'});

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
    <html lang="en" suppressHydrationWarning className={cn("font-mono", jetbrainsMono.variable, merriweatherHeading.variable)}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
