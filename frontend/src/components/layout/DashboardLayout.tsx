'use client'

import { ReactNode } from 'react'
import { Sidebar } from './Sidebar'

interface DashboardLayoutProps {
  children: ReactNode
  title?: string
  subtitle?: string
}

export function DashboardLayout({ children, title, subtitle }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-64 p-8">
        {(title || subtitle) && (
          <div className="mb-8">
            {title && (
              <h1 className="text-3xl font-heading font-bold text-foreground" data-testid="page-title">
                {title}
              </h1>
            )}
            {subtitle && (
              <p className="mt-2 text-muted-foreground" data-testid="page-subtitle">
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
