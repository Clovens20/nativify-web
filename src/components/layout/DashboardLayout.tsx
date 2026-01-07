'use client'

import { ReactNode, useState } from 'react'
import { Sidebar } from './Sidebar'
import { Button } from '@/components/ui/button'
import { Menu, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DashboardLayoutProps {
  children: ReactNode
  title?: string
  subtitle?: string
}

export function DashboardLayout({ children, title, subtitle }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 md:hidden bg-background-paper/80 backdrop-blur-xl border border-white/10"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle menu"
      >
        {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-40 transform transition-transform duration-300 ease-in-out md:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <Sidebar onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="md:ml-64 p-4 md:p-8 pt-16 md:pt-8">
        {(title || subtitle) && (
          <div className="mb-6 md:mb-8">
            {title && (
              <h1 className="text-2xl md:text-3xl font-heading font-bold text-foreground" data-testid="page-title">
                {title}
              </h1>
            )}
            {subtitle && (
              <p className="mt-2 text-sm md:text-base text-muted-foreground" data-testid="page-subtitle">
                {subtitle}
              </p>
            )}
          </div>
        )}
        {children}
      </main>
    </div>
  )
}
