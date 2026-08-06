'use client'

import { CaretDown, Sun, Moon, List, TextAlignLeft } from '@phosphor-icons/react'
import { usePathname, useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/lib/utils'
import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/shared/ui/dropdown-menu'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/shared/ui/sheet'
import { NAV_ITEMS } from './nav-items'

const GenerationHistoryDrawer = dynamic(() => import('@/shared/components/GenerationHistoryDrawer'), { ssr: false })

export default function Header() {
  const pathname = usePathname()
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const currentTab = pathname?.split('/')[1] || 'jobs'
  const currentSubTab = pathname?.split('/')[2] || null

  useEffect(() => setMounted(true), [])

  const go = (id: string, childId?: string) => {
    router.push(childId ? `/${id}/${childId}` : `/${id}`)
    setMobileNavOpen(false)
  }

  return (
    <>
      <header className="h-12 border-b flex items-center px-3 md:px-4 gap-2 md:gap-4 shrink-0 fixed top-0 left-0 right-0 z-40 bg-card">
        <button
          className="md:hidden flex items-center justify-center w-8 h-8 rounded-md border border-border bg-card text-muted-foreground hover:text-foreground"
          onClick={() => setMobileNavOpen(true)}
          aria-label="Open navigation menu"
        >
          <TextAlignLeft className="w-4 h-4" />
        </button>

        <span
          className="font-extrabold text-sm bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent whitespace-nowrap cursor-pointer hover:opacity-80 transition-opacity"
          onClick={() => router.push('/jobs')}
        >
          Job Search
        </span>

        <nav className="hidden md:flex items-center gap-1" aria-label="Main navigation">
          {NAV_ITEMS.map(item => {
            const Icon = item.icon
            const isActive = currentTab === item.id
            const hasChildren = !!item.children?.length

            const base = cn(
              "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all",
              isActive ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground hover:bg-muted"
            )

            if (hasChildren) {
              return (
                <DropdownMenu key={item.id}>
                  <DropdownMenuTrigger asChild>
                    <button className={base}>
                      <Icon className={cn("w-3.5 h-3.5", isActive ? "text-primary" : item.color)} />
                      {item.label}
                      <CaretDown className={cn("w-3 h-3", isActive ? "text-primary" : "text-muted-foreground")} weight="bold" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="min-w-[12rem]">
                    {item.children!.map(child => {
                      const childActive = currentSubTab === child.id && isActive
                      return (
                        <DropdownMenuItem
                          key={child.id}
                          onClick={() => go(item.id, child.id)}
                          className={cn("cursor-pointer", childActive && "bg-primary/10 text-primary font-semibold")}
                        >
                          {child.label}
                        </DropdownMenuItem>
                      )
                    })}
                  </DropdownMenuContent>
                </DropdownMenu>
              )
            }

            return (
              <button key={item.id} onClick={() => go(item.id)} className={base}>
                <Icon className={cn("w-3.5 h-3.5", isActive ? "text-primary" : item.color)} />
                {item.label}
              </button>
            )
          })}
        </nav>

        <div className="ml-auto flex items-center gap-1.5">
          {mounted && (
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
          )}
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setHistoryOpen(true)} title="Generation History">
            <List className="w-4 h-4" />
          </Button>
        </div>
      </header>

      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-64 p-0">
          <SheetHeader className="border-b px-4 py-3">
            <SheetTitle className="font-extrabold text-sm bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
              Job Search
            </SheetTitle>
          </SheetHeader>
          <nav className="p-2 space-y-0.5" aria-label="Mobile navigation">
            {NAV_ITEMS.map(item => {
              const Icon = item.icon
              const isActive = currentTab === item.id
              return (
                <div key={item.id}>
                  <button
                    onClick={() => go(item.id)}
                    className={cn(
                      "flex items-center gap-2 w-full px-3 py-2 text-sm rounded-md transition-colors",
                      isActive ? "bg-primary/10 font-semibold text-primary" : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    )}
                  >
                    <Icon className={cn("w-4 h-4", isActive ? "text-primary" : item.color)} />
                    {item.label}
                  </button>
                  {item.children?.map(child => {
                    const childActive = currentSubTab === child.id && isActive
                    return (
                      <button
                        key={child.id}
                        onClick={() => go(item.id, child.id)}
                        className={cn(
                          "flex items-center gap-2 pl-9 pr-3 py-1.5 text-xs rounded-md transition-colors",
                          childActive ? "bg-primary/10 font-semibold text-primary" : "text-muted-foreground hover:text-foreground hover:bg-muted"
                        )}
                      >
                        {child.label}
                      </button>
                    )
                  })}
                </div>
              )
            })}
          </nav>
        </SheetContent>
      </Sheet>

      <GenerationHistoryDrawer open={historyOpen} onOpenChange={setHistoryOpen} />
    </>
  )
}
