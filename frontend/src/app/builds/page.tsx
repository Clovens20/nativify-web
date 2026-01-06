'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { buildsApi, projectsApi } from '@/lib/api'
import { 
  Smartphone, 
  Apple, 
  Download,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'

interface Build {
  id: string
  project_id: string
  platform: string
  status: string
  phase: string
  progress: number
  created_at: string
  completed_at: string | null
  duration_seconds: number | null
}

interface Project {
  id: string
  name: string
}

export default function BuildsPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [builds, setBuilds] = useState<Build[]>([])
  const [projects, setProjects] = useState<Record<string, Project>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    const fetchData = async () => {
      if (!user?.id) return
      try {
        const [buildsData, projectsData] = await Promise.all([
          buildsApi.getAll(user.id),
          projectsApi.getAll(user.id)
        ])
        setBuilds(buildsData)
        
        // Create a map of projects
        const projectsMap: Record<string, Project> = {}
        projectsData.forEach((p: Project) => {
          projectsMap[p.id] = p
        })
        setProjects(projectsMap)
      } catch (error) {
        console.error('Failed to fetch builds:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [user])

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success" className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Completed</Badge>
      case 'processing':
        return <Badge className="flex items-center gap-1 bg-primary/20 text-primary"><Loader2 className="w-3 h-3 animate-spin" /> Processing</Badge>
      case 'failed':
        return <Badge variant="destructive" className="flex items-center gap-1"><XCircle className="w-3 h-3" /> Failed</Badge>
      default:
        return <Badge variant="warning" className="flex items-center gap-1"><AlertCircle className="w-3 h-3" /> Pending</Badge>
    }
  }

  return (
    <DashboardLayout title="Builds" subtitle="View all your build history">
      <Card className="bg-background-paper border-white/10">
        <CardHeader>
          <CardTitle>Build History</CardTitle>
          <CardDescription>All builds across your projects</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : builds.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-muted-foreground">No builds yet</p>
              <p className="text-sm text-muted-foreground mt-1">Start a build from one of your projects</p>
            </div>
          ) : (
            <div className="space-y-4">
              {builds.map((build) => (
                <div
                  key={build.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-white/10 hover:border-white/20 transition-colors"
                  data-testid={`build-${build.id}`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                      build.platform === 'android' ? 'bg-success/10' : 'bg-info/10'
                    }`}>
                      {build.platform === 'android' ? (
                        <Smartphone className="w-6 h-6 text-success" />
                      ) : (
                        <Apple className="w-6 h-6 text-info" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">
                        {projects[build.project_id]?.name || 'Unknown Project'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {build.platform.charAt(0).toUpperCase() + build.platform.slice(1)} Build
                      </p>
                      <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                        <Clock className="w-3 h-3" />
                        {new Date(build.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {build.status === 'processing' && (
                      <div className="w-32">
                        <Progress value={build.progress} className="h-2" />
                        <p className="text-xs text-muted-foreground text-center mt-1">{build.progress}%</p>
                      </div>
                    )}
                    
                    {getStatusBadge(build.status)}
                    
                    {build.status === 'completed' && (
                      <a href={buildsApi.download(build.id, user.id)} download>
                        <Button size="sm" variant="outline" className="border-white/10">
                          <Download className="w-4 h-4 mr-1" />
                          Download
                        </Button>
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </DashboardLayout>
  )
}
