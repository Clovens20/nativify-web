'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { projectsApi } from '@/lib/api'
import { toast } from 'sonner'
import { 
  Plus, 
  Globe, 
  Smartphone,
  MoreVertical,
  Trash2,
  Loader2
} from 'lucide-react'

interface Project {
  id: string
  name: string
  web_url: string
  description: string
  platform: string[]
  status: string
  created_at: string
}

export default function ProjectsPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    const fetchProjects = async () => {
      if (!user?.id) return
      try {
        const data = await projectsApi.getAll()
        setProjects(data)
      } catch (error) {
        console.error('Failed to fetch projects:', error)
        toast.error('Failed to load projects')
      } finally {
        setLoading(false)
      }
    }
    fetchProjects()
  }, [user])

  const handleDelete = async (projectId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!user?.id) return
    
    if (!confirm('Are you sure you want to delete this project?')) return
    
    try {
      await projectsApi.delete(projectId)
      setProjects(projects.filter(p => p.id !== projectId))
      toast.success('Project deleted')
    } catch (error) {
      toast.error('Failed to delete project')
    }
  }

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <DashboardLayout title="Projects" subtitle="Manage your NativiWeb projects">
      <div className="flex justify-end mb-6">
        <Link href="/projects/new">
          <Button className="bg-primary text-black font-bold hover:bg-primary-hover" data-testid="create-project-btn">
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : projects.length === 0 ? (
        <Card className="bg-background-paper border-white/10">
          <CardContent className="py-20 text-center">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <Smartphone className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-xl font-heading font-bold mb-2">No projects yet</h3>
            <p className="text-muted-foreground mb-6">Create your first project to get started</p>
            <Link href="/projects/new">
              <Button className="bg-primary text-black font-bold">
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Project
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`}>
              <Card className="bg-background-paper border-white/10 hover:border-primary/30 transition-all h-full" data-testid={`project-card-${project.id}`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center">
                      <Globe className="w-6 h-6 text-primary" />
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-destructive"
                      onClick={(e) => handleDelete(project.id, e)}
                      data-testid={`delete-project-${project.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                  
                  <h3 className="font-heading font-bold text-lg mb-1">{project.name}</h3>
                  <p className="text-sm text-muted-foreground truncate mb-3">{project.web_url}</p>
                  
                  {project.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-4">{project.description}</p>
                  )}
                  
                  <div className="flex items-center justify-between">
                    <div className="flex gap-2">
                      {project.platform.includes('android') && (
                        <Badge variant="outline" className="text-success border-success/30">Android</Badge>
                      )}
                      {project.platform.includes('ios') && (
                        <Badge variant="outline" className="text-info border-info/30">iOS</Badge>
                      )}
                    </div>
                    <Badge variant={project.status === 'active' ? 'success' : 'warning'}>
                      {project.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </DashboardLayout>
  )
}
