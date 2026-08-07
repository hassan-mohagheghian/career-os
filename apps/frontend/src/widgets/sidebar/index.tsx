'use client'

import { useState, useEffect, type ReactNode } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import dynamic from 'next/dynamic'
import {
  CaretDown,
  Sun,
  Moon,
  List,
  TextAlignLeft,
  SidebarSimple,
  Briefcase,
} from '@phosphor-icons/react'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/shared/ui/tooltip'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/shared/ui/sheet'
import { NAV_ITEMS, type NavItem } from './nav-items'

const GenerationHistoryDrawer = dynamic(() => import('@/shared/components/GenerationHistoryDrawer'), { ssr: false })

const COLLAPSE_KEY = 'job-search.sidebar.collapsed'

function BrandMark() {
  return (
    <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-primary text-primary-foreground shrink-0">
      <Briefcase className="w-4 h-4" weight="fill" />
    </span>
  )
}

function NavRow({
  item,
  currentTab,
  currentSubTab,
  aiOpen,
  collapsed,
  onNavigate,
  onToggleAI,
  onExpand,
}: {
  item: NavItem
  currentTab: string
  currentSubTab: string | null
  aiOpen: boolean
  collapsed: boolean
  onNavigate: (id: string, childId?: string) => void
  onToggleAI: () => void
  onExpand: () => void
}) {
  const Icon = item.icon
  const isActive = currentTab === item.id
  const hasChildren = !!item.children?.length

  const handleClick = () => {
    if (hasChildren) {
      if (collapsed) onExpand()
      else onToggleAI()
      return
    }
    onNavigate(item.id)
  }

  const row = (
    <button
      onClick={handleClick}
      aria-expanded={hasChildren ? aiOpen : undefined}
      className={cn(
        "relative flex items-center gap-2.5 w-full rounded-lg px-2.5 py-2 text-sm font-medium transition-colors",
        collapsed && "justify-center px-0",
        isActive
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:text-foreground hover:bg-muted"
      )}
    >
      {isActive && !collapsed && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 rounded-full bg-primary" aria-hidden />
      )}
      <Icon className="w-[18px] h-[18px] shrink-0" />
      {!collapsed && <span className="flex-1 text-left truncate">{item.label}</span>}
      {hasChildren && !collapsed && (
        <CaretDown
          className={cn(
            "w-3.5 h-3.5 shrink-0 transition-transform",
            aiOpen && "rotate-180",
            isActive ? "text-primary" : "text-muted-foreground"
          )}
          weight="bold"
        />
      )}
    </button>
  )

  return (
    <div>
      {collapsed ? (
        <Tooltip>
          <TooltipTrigger asChild>{row}</TooltipTrigger>
          <TooltipContent side="right">{item.label}</TooltipContent>
        </Tooltip>
      ) : (
        row
      )}
      {hasChildren && aiOpen && !collapsed && (
        <div className="ml-4 border-l border-border pl-3 mt-0.5 space-y-0.5">
          {item.children!.map(child => {
            const childActive = currentSubTab === child.id && isActive
            return (
              <button
                key={child.id}
                onClick={() => onNavigate(item.id, child.id)}
                className={cn(
                  "w-full text-left px-2 py-1.5 rounded-md text-xs transition-colors",
                  childActive
                    ? "bg-primary/10 text-primary font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                )}
              >
                {child.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme()
  return (
    <Button
      variant="ghost"
      size="icon"
      className={className}
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      title="Toggle theme"
    >
      {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
    </Button>
  )
}

export default function Sidebar({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [aiOpen, setAiOpen] = useState(false)
  const [mobileAiOpen, setMobileAiOpen] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const currentTab = pathname?.split('/')[1] || 'jobs'
  const currentSubTab = pathname?.split('/')[2] || null

  useEffect(() => {
    setMounted(true)
    if (typeof window !== 'undefined' && window.localStorage.getItem(COLLAPSE_KEY) === 'collapsed') {
      setCollapsed(true)
    }
  }, [])

  const toggleCollapsed = () => {
    setCollapsed(prev => {
      const next = !prev
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(COLLAPSE_KEY, next ? 'collapsed' : 'expanded')
      }
      return next
    })
  }

  const go = (id: string, childId?: string) => {
    router.push(childId ? `/${id}/${childId}` : `/${id}`)
    setMobileNavOpen(false)
  }

  const expandSidebar = () => {
    setCollapsed(false)
    setAiOpen(true)
  }

  const navProps = {
    currentTab,
    currentSubTab,
    onNavigate: go,
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <div className="hidden lg:flex flex-col h-full shrink-0 border-r bg-card">
        <div className="flex items-center h-14 shrink-0 px-3 gap-2 border-b">
          <BrandMark />
          {!collapsed && (
            <span
              className="font-extrabold text-sm text-primary whitespace-nowrap cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => router.push('/jobs')}
            >
              Job Search
            </span>
          )}
        </div>

        <nav
          aria-label="Main navigation"
          className={cn("flex-1 overflow-y-auto p-2 space-y-0.5", collapsed && "px-1.5")}
        >
          {NAV_ITEMS.map(item => (
            <NavRow
              key={item.id}
              item={item}
              aiOpen={aiOpen}
              collapsed={collapsed}
              onToggleAI={() => setAiOpen(o => !o)}
              onExpand={expandSidebar}
              {...navProps}
            />
          ))}
        </nav>

        <div className={cn("shrink-0 border-t p-2 space-y-1", collapsed && "px-1.5")}>
          <div className={cn("flex items-center justify-center gap-1", collapsed && "flex-col")}>
            {mounted && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="inline-flex">
                    <ThemeToggle className={collapsed ? "w-11 h-10" : "h-9 w-9"} />
                  </span>
                </TooltipTrigger>
                <TooltipContent side="right">Toggle theme</TooltipContent>
              </Tooltip>
            )}
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="inline-flex">
                  <Button
                    variant="ghost"
                    size="icon"
                    className={collapsed ? "w-11 h-10" : "h-9 w-9"}
                    onClick={() => setHistoryOpen(true)}
                    title="Generation History"
                  >
                    <List className="w-4 h-4" />
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent side="right">Generation History</TooltipContent>
            </Tooltip>
          </div>
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-flex w-full">
                <Button
                  variant="ghost"
                  className={cn(
                    "text-muted-foreground hover:text-foreground",
                    collapsed ? "w-11 h-10 justify-center px-0 mx-auto" : "w-full justify-center gap-2"
                  )}
                  onClick={toggleCollapsed}
                  title="Collapse sidebar"
                >
                  <SidebarSimple className={cn("w-4 h-4", collapsed && "rotate-180")} />
                  {!collapsed && <span className="text-xs">Collapse</span>}
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent side="right">{collapsed ? 'Expand sidebar' : 'Collapse sidebar'}</TooltipContent>
          </Tooltip>
        </div>
      </div>

      <div className="flex flex-col flex-1 min-w-0">
        <header className="lg:hidden h-12 border-b flex items-center px-3 gap-2 shrink-0 bg-card">
          <button
            className="flex items-center justify-center w-8 h-8 rounded-md border border-border bg-card text-muted-foreground hover:text-foreground"
            onClick={() => setMobileNavOpen(true)}
            aria-label="Open navigation menu"
          >
            <TextAlignLeft className="w-4 h-4" />
          </button>
          <span
            className="font-extrabold text-sm text-primary whitespace-nowrap cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => router.push('/jobs')}
          >
            Job Search
          </span>
          <div className="ml-auto flex items-center gap-1.5">
            {mounted && <ThemeToggle className="h-8 w-8 border" />}
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setHistoryOpen(true)} title="Generation History">
              <List className="w-4 h-4" />
            </Button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4">
          <div className="max-w-[1400px] mx-auto h-full">
            {children}
          </div>
        </main>
      </div>

      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-72 p-0 flex flex-col">
          <SheetHeader className="border-b px-4 py-3 shrink-0">
            <SheetTitle className="flex items-center gap-2 font-extrabold text-sm">
              <BrandMark />
              <span className="text-primary font-extrabold">Job Search</span>
            </SheetTitle>
          </SheetHeader>
          <nav aria-label="Mobile navigation" className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {NAV_ITEMS.map(item => (
              <NavRow
                key={item.id}
                item={item}
                aiOpen={mobileAiOpen}
                collapsed={false}
                onToggleAI={() => setMobileAiOpen(o => !o)}
                onExpand={() => setMobileAiOpen(true)}
                {...navProps}
              />
            ))}
          </nav>
          <div className="border-t p-2 flex items-center justify-center gap-1 shrink-0">
            {mounted && <ThemeToggle className="h-9 w-9" />}
            <Button variant="ghost" size="icon" className="h-9 w-9" onClick={() => setHistoryOpen(true)} title="Generation History">
              <List className="w-4 h-4" />
            </Button>
          </div>
        </SheetContent>
      </Sheet>

      <GenerationHistoryDrawer open={historyOpen} onOpenChange={setHistoryOpen} />
    </div>
  )
}
