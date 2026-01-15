'use client'

import { ReactNode } from 'react'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { 
  Shield, 
  LayoutDashboard, 
  LogOut,
  Menu,
  X,
  Users,
  FolderKanban,
  Hammer,
  FileText,
  BarChart3,
  FileCode,
  Key,
  Settings,
  Activity,
  ArrowLeft
} from 'lucide-react'
import { useState } from 'react'
import { Badge } from '@/components/ui/badge'

interface AdminLayoutProps {
  children: ReactNode
  title?: string
  activeTab?: string
  onTabChange?: (tab: string) => void
}

export function AdminLayout({ children, title = 'Admin Panel', activeTab, onTabChange }: AdminLayoutProps) {
  const { user, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  
  const handleNavClick = (tab: string) => {
    if (onTabChange) {
      onTabChange(tab)
      // Close sidebar on mobile after navigation
      if (window.innerWidth < 1024) {
        setSidebarOpen(false)
      }
    }
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 bg-background-paper border-r border-white/10
        transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-destructive/20 border border-destructive/50 flex items-center justify-center">
                  <Shield className="w-6 h-6 text-destructive" />
                </div>
                <div>
                  <h1 className="font-bold text-lg">Admin Panel</h1>
                  <p className="text-xs text-muted-foreground">NativiWeb Studio</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
            
            {user && (
              <div className="pt-4 border-t border-white/10">
                <p className="text-sm font-medium">{user.name}</p>
                <p className="text-xs text-muted-foreground">{user.email}</p>
                <Badge variant="destructive" className="mt-2">
                  Administrator
                </Badge>
              </div>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-1">
            <Button 
              variant={activeTab === 'dashboard' ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => handleNavClick('dashboard')}
            >
              <LayoutDashboard className="w-4 h-4 mr-2" />
              Tableau de bord
            </Button>
            <Button 
              variant={activeTab === 'users' ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => handleNavClick('users')}
            >
              <Users className="w-4 h-4 mr-2" />
              Utilisateurs
            </Button>
            <Button 
              variant={activeTab === 'projects' ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => handleNavClick('projects')}
            >
              <FolderKanban className="w-4 h-4 mr-2" />
              Projets
            </Button>
            <Button 
              variant={activeTab === 'builds' ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => handleNavClick('builds')}
            >
              <Hammer className="w-4 h-4 mr-2" />
              Builds
            </Button>
            <Button 
              variant={activeTab === 'logs' ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => handleNavClick('logs')}
            >
              <FileText className="w-4 h-4 mr-2" />
              Logs Système
            </Button>
            <Button 
              variant={activeTab === 'analytics' ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => handleNavClick('analytics')}
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Analytics
            </Button>
            <Button 
              variant={activeTab === 'templates' ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => handleNavClick('templates')}
            >
              <FileCode className="w-4 h-4 mr-2" />
              Templates
            </Button>
            <Button 
              variant={activeTab === 'api-keys' ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => handleNavClick('api-keys')}
            >
              <Key className="w-4 h-4 mr-2" />
              API Keys
            </Button>
            <Button 
              variant={activeTab === 'monitoring' ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => handleNavClick('monitoring')}
            >
              <Activity className="w-4 h-4 mr-2" />
              Monitoring
            </Button>
            <Button 
              variant={activeTab === 'config' ? 'secondary' : 'ghost'}
              className="w-full justify-start"
              onClick={() => handleNavClick('config')}
            >
              <Settings className="w-4 h-4 mr-2" />
              Configuration
            </Button>
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-white/10">
            <Link href="/dashboard">
              <Button variant="outline" className="w-full mb-2">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Retour Dashboard
              </Button>
            </Link>
            <Button 
              variant="ghost" 
              className="w-full text-destructive hover:text-destructive"
              onClick={logout}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Déconnexion
            </Button>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-xl border-b border-white/10 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden"
                onClick={() => setSidebarOpen(true)}
              >
                <Menu className="w-5 h-5" />
              </Button>
              <div>
                <h2 className="text-2xl font-heading font-bold">{title}</h2>
                <p className="text-sm text-muted-foreground">Administration de la plateforme</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/30">
                <Shield className="w-3 h-3 mr-1" />
                Mode Admin
              </Badge>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="p-4 md:p-6">
          {children}
        </div>
      </main>
    </div>
  )
}

