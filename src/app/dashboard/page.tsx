'use client'

import { useEffect, useState, useCallback, useMemo } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { statsApi, projectsApi, buildsApi } from '@/lib/api'
import { logger } from '@/lib/logger'
import { 
  FolderKanban, 
  Hammer, 
  Key, 
  CheckCircle2,
  Plus,
  ArrowRight,
  Loader2
} from 'lucide-react'

interface Stats {
  projects: number
  total_builds: number
  successful_builds: number
  api_keys: number
}

interface Project {
  id: string
  name: string
  web_url: string
  status: string
  created_at: string
}

interface Build {
  id: string
  project_id: string
  platform: string
  status: string
  progress: number
  created_at: string
}

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [stats, setStats] = useState<Stats | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [recentBuilds, setRecentBuilds] = useState<Build[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  const fetchData = useCallback(async () => {
    if (!user?.id) return
    try {
      const [statsData, projectsData, buildsData] = await Promise.all([
        statsApi.get(),
        projectsApi.getAll(),
        buildsApi.getAll()
      ])
      setStats(statsData)
      setProjects(projectsData.slice(0, 3))
      setRecentBuilds(buildsData.slice(0, 5))
    } catch (error) {
      logger.error('Failed to fetch dashboard data', error, { userId: user?.id })
    } finally {
      setLoading(false)
    }
  }, [user?.id])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // useMemo doit être appelé AVANT tout return conditionnel (règle des hooks React)
  const statCards = useMemo(() => [
    { label: 'Projects', value: stats?.projects || 0, icon: FolderKanban, color: 'primary' },
    { label: 'Total Builds', value: stats?.total_builds || 0, icon: Hammer, color: 'secondary' },
    { label: 'Successful', value: stats?.successful_builds || 0, icon: CheckCircle2, color: 'success' },
    { label: 'API Keys', value: stats?.api_keys || 0, icon: Key, color: 'warning' },
  ], [stats])

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <DashboardLayout title={`Welcome back, ${user.name}`} subtitle="Here's an overview of your NativiWeb projects">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.label} className="bg-background-paper border-white/10" data-testid={`stat-${stat.label.toLowerCase()}`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                    <p className="text-3xl font-bold mt-1">
                      {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : stat.value}
                    </p>
                  </div>
                  <div className={`w-12 h-12 rounded-lg bg-${stat.color}/10 flex items-center justify-center`}>
                    <Icon className={`w-6 h-6 text-${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Quick Actions */}
      <Card className="bg-background-paper border-white/10 mb-8">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Get started with your next native app</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Link href="/projects/new">
              <Button className="bg-primary text-black font-bold hover:bg-primary-hover" data-testid="new-project-btn">
                <Plus className="w-4 h-4 mr-2" />
                New Project
              </Button>
            </Link>
            <Link href="/docs">
              <Button variant="outline" className="border-white/10" data-testid="docs-btn">
                View Documentation
              </Button>
            </Link>
            <Link href="/api-keys">
              <Button variant="outline" className="border-white/10" data-testid="api-keys-btn">
                <Key className="w-4 h-4 mr-2" />
                Manage API Keys
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Projects */}
        <Card className="bg-background-paper border-white/10">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Projects</CardTitle>
              <CardDescription>Your latest projects</CardDescription>
            </div>
            <Link href="/projects">
              <Button variant="ghost" size="sm" className="text-primary">
                View All <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
              </div>
            ) : projects.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">No projects yet</p>
                <Link href="/projects/new">
                  <Button size="sm" className="bg-primary text-black">
                    <Plus className="w-4 h-4 mr-2" />
                    Create Your First Project
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {projects.map((project) => (
                  <Link key={project.id} href={`/projects/${project.id}`}>
                    <div className="flex items-center justify-between p-3 rounded-lg border border-white/5 hover:border-primary/30 transition-colors" data-testid={`project-${project.id}`}>
                      <div>
                        <p className="font-medium">{project.name}</p>
                        <p className="text-sm text-muted-foreground truncate max-w-[200px]">{project.web_url}</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        project.status === 'active' ? 'bg-success/20 text-success' : 'bg-warning/20 text-warning'
                      }`}>
                        {project.status}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Builds */}
        <Card className="bg-background-paper border-white/10">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Builds</CardTitle>
              <CardDescription>Latest build activity</CardDescription>
            </div>
            <Link href="/builds">
              <Button variant="ghost" size="sm" className="text-primary">
                View All <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
              </div>
            ) : recentBuilds.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">No builds yet</p>
                <p className="text-sm text-muted-foreground mt-1">Create a project and start a build</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentBuilds.map((build) => (
                  <div key={build.id} className="flex items-center justify-between p-3 rounded-lg border border-white/5" data-testid={`build-${build.id}`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold ${
                        build.platform === 'android' ? 'bg-success/20 text-success' : 'bg-info/20 text-info'
                      }`}>
                        {build.platform === 'android' ? 'AND' : 'iOS'}
                      </div>
                      <div>
                        <p className="text-sm font-medium">Build #{build.id.slice(0, 8)}</p>
                        <p className="text-xs text-muted-foreground">{build.platform}</p>
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      build.status === 'completed' ? 'bg-success/20 text-success' :
                      build.status === 'processing' ? 'bg-primary/20 text-primary' :
                      build.status === 'failed' ? 'bg-destructive/20 text-destructive' :
                      'bg-warning/20 text-warning'
                    }`}>
                      {build.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
