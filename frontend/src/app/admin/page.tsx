'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { adminApi } from '@/lib/api'
import { toast } from 'sonner'
import { 
  Users, 
  Hammer, 
  FileText,
  BarChart3,
  Loader2,
  Ban,
  CheckCircle2,
  Shield
} from 'lucide-react'

interface User {
  id: string
  email: string
  name: string
  role: string
  status: string
  created_at: string
  projects_count: number
  builds_count: number
}

interface Build {
  id: string
  project_id: string
  platform: string
  status: string
  project_name: string
  user_name: string
  user_email: string
  created_at: string
}

interface Log {
  id: string
  level: string
  category: string
  message: string
  created_at: string
}

interface Analytics {
  users: { total: number; active: number }
  projects: { total: number }
  builds: { total: number; successful: number; failed: number; success_rate: number }
  platforms: { android: number; ios: number }
}

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [builds, setBuilds] = useState<Build[]>([])
  const [logs, setLogs] = useState<Log[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    const fetchData = async () => {
      if (!user?.id) return
      
      // Check if user is admin
      if (user.role !== 'admin') {
        toast.error('Admin access required')
        router.push('/dashboard')
        return
      }

      try {
        const [usersData, buildsData, logsData, analyticsData] = await Promise.all([
          adminApi.getUsers(user.id),
          adminApi.getBuilds(user.id),
          adminApi.getLogs(user.id),
          adminApi.getAnalytics(user.id)
        ])
        setUsers(usersData.users || [])
        setBuilds(buildsData.builds || [])
        setLogs(logsData.logs || [])
        setAnalytics(analyticsData)
      } catch (error: any) {
        if (error.response?.status === 403) {
          toast.error('Admin access required')
          router.push('/dashboard')
        } else {
          console.error('Failed to fetch admin data:', error)
        }
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [user, router])

  const handleBanUser = async (userId: string) => {
    if (!user?.id) return
    try {
      await adminApi.updateUser(userId, user.id, { status: 'banned' })
      setUsers(users.map(u => u.id === userId ? { ...u, status: 'banned' } : u))
      toast.success('User banned')
    } catch (error) {
      toast.error('Failed to ban user')
    }
  }

  const handleUnbanUser = async (userId: string) => {
    if (!user?.id) return
    try {
      await adminApi.updateUser(userId, user.id, { status: 'active' })
      setUsers(users.map(u => u.id === userId ? { ...u, status: 'active' } : u))
      toast.success('User unbanned')
    } catch (error) {
      toast.error('Failed to unban user')
    }
  }

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  if (user.role !== 'admin') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Shield className="w-16 h-16 text-destructive mx-auto mb-4" />
          <h1 className="text-2xl font-bold mb-2">Access Denied</h1>
          <p className="text-muted-foreground">You need admin privileges to access this page.</p>
        </div>
      </div>
    )
  }

  return (
    <DashboardLayout title="Admin Panel" subtitle="Manage platform users and settings">
      {/* Analytics Overview */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-background-paper border-white/10">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Users</p>
                  <p className="text-3xl font-bold">{analytics.users.total}</p>
                  <p className="text-xs text-muted-foreground">{analytics.users.active} active</p>
                </div>
                <Users className="w-8 h-8 text-primary" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-background-paper border-white/10">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Projects</p>
                  <p className="text-3xl font-bold">{analytics.projects.total}</p>
                </div>
                <BarChart3 className="w-8 h-8 text-secondary" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-background-paper border-white/10">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Builds</p>
                  <p className="text-3xl font-bold">{analytics.builds.total}</p>
                  <p className="text-xs text-muted-foreground">{analytics.builds.success_rate}% success</p>
                </div>
                <Hammer className="w-8 h-8 text-success" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-background-paper border-white/10">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Platforms</p>
                  <p className="text-sm">Android: {analytics.platforms.android}</p>
                  <p className="text-sm">iOS: {analytics.platforms.ios}</p>
                </div>
                <FileText className="w-8 h-8 text-warning" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="users" className="space-y-6">
        <TabsList className="bg-background-subtle">
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="builds">Builds</TabsTrigger>
          <TabsTrigger value="logs">System Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>User Management</CardTitle>
              <CardDescription>Manage platform users</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-10">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <div className="space-y-3">
                    {users.map((u) => (
                      <div key={u.id} className="flex items-center justify-between p-4 rounded-lg border border-white/10">
                        <div>
                          <p className="font-medium">{u.name}</p>
                          <p className="text-sm text-muted-foreground">{u.email}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant={u.role === 'admin' ? 'default' : 'outline'}>
                              {u.role}
                            </Badge>
                            <Badge variant={u.status === 'active' ? 'success' : 'destructive'}>
                              {u.status}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            {u.projects_count} projects • {u.builds_count} builds
                          </p>
                        </div>
                        <div className="flex gap-2">
                          {u.status === 'active' ? (
                            <Button
                              size="sm"
                              variant="outline"
                              className="border-destructive/30 text-destructive hover:bg-destructive/10"
                              onClick={() => handleBanUser(u.id)}
                              disabled={u.role === 'admin'}
                            >
                              <Ban className="w-4 h-4 mr-1" />
                              Ban
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              className="border-success/30 text-success hover:bg-success/10"
                              onClick={() => handleUnbanUser(u.id)}
                            >
                              <CheckCircle2 className="w-4 h-4 mr-1" />
                              Unban
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="builds">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>Build History</CardTitle>
              <CardDescription>All builds across the platform</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {builds.map((build) => (
                    <div key={build.id} className="flex items-center justify-between p-4 rounded-lg border border-white/10">
                      <div>
                        <p className="font-medium">{build.project_name}</p>
                        <p className="text-sm text-muted-foreground">by {build.user_name}</p>
                        <p className="text-xs text-muted-foreground">{new Date(build.created_at).toLocaleString()}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{build.platform}</Badge>
                        <Badge variant={build.status === 'completed' ? 'success' : build.status === 'failed' ? 'destructive' : 'default'}>
                          {build.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>System Logs</CardTitle>
              <CardDescription>Platform activity logs</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-2">
                  {logs.map((log) => (
                    <div key={log.id} className="p-3 rounded-lg border border-white/10 font-mono text-sm">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={log.level === 'error' ? 'destructive' : log.level === 'warning' ? 'warning' : 'default'} className="text-xs">
                          {log.level}
                        </Badge>
                        <Badge variant="outline" className="text-xs">{log.category}</Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-muted-foreground">{log.message}</p>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  )
}
