import type { ReactNode } from 'react'

interface DashboardLayoutProps {
  sidebar: ReactNode
  children: ReactNode
}

export default function DashboardLayout({ sidebar, children }: DashboardLayoutProps) {
  return (
    <div className="flex h-svh flex-col overflow-hidden bg-background">
      {/* Header */}
      <header className="flex h-14 shrink-0 items-center border-b border-border px-6">
        <h1 className="text-lg font-semibold tracking-tight">
          BlueBridge
        </h1>
        <span className="ml-2 text-xs text-teal font-medium tracking-widest uppercase opacity-70">
          Termsheet Manager
        </span>
      </header>

      {/* Body: sidebar + main */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="flex w-72 shrink-0 flex-col overflow-y-auto border-r border-border bg-secondary/50">
          {sidebar}
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-4xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
