'use client'

import { useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { useDebounce } from '@/hooks/useDebounce'
import { AdminLayout } from '@/components/layout/AdminLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { adminApi, featuresApi } from '@/lib/api'
import { toast } from 'sonner'
import { logger } from '@/lib/logger'
import { 
  Users, 
  Hammer, 
  FileText,
  BarChart3,
  Loader2,
  Ban,
  CheckCircle2,
  Shield,
  Settings,
  Search,
  ChevronLeft,
  ChevronRight,
  Filter,
  Download,
  RefreshCw,
  Plus,
  Edit,
  Trash2,
  FolderKanban,
  FileCode,
  Key,
  Activity,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  UserPlus,
  Eye,
  MoreVertical,
  Globe
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

interface VisitStats {
  total_visits: number
  unique_visitors: number
  visits_today: number
  visits_this_week: number
  visits_this_month: number
  top_pages: Array<{ path: string; count: number }>
  device_breakdown: Record<string, number>
}

interface PlatformConfig {
  maintenance_mode: boolean
  max_builds_per_user: number
  max_projects_per_user: number
  allowed_domains: string[]
  build_timeout_minutes: number
}

interface PaginatedResponse {
  users?: User[]
  builds?: Build[]
  logs?: Log[]
  total: number
  page: number
  pages: number
}

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [projects, setProjects] = useState<any[]>([])
  const [builds, setBuilds] = useState<Build[]>([])
  const [logs, setLogs] = useState<Log[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [visitStats, setVisitStats] = useState<VisitStats | null>(null)
  const [config, setConfig] = useState<PlatformConfig | null>(null)
  const [loading, setLoading] = useState(true)
  
  // Projects pagination
  const [projectsPage, setProjectsPage] = useState(1)
  const [projectsTotal, setProjectsTotal] = useState(0)
  const [projectsPages, setProjectsPages] = useState(1)
  
  // User management states
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [showEditUser, setShowEditUser] = useState<User | null>(null)
  const [newUserData, setNewUserData] = useState({ email: '', password: '', name: '', role: 'user' })
  
  // Pagination states
  const [usersPage, setUsersPage] = useState(1)
  const [buildsPage, setBuildsPage] = useState(1)
  const [logsPage, setLogsPage] = useState(1)
  const [usersTotal, setUsersTotal] = useState(0)
  const [buildsTotal, setBuildsTotal] = useState(0)
  const [logsTotal, setLogsTotal] = useState(0)
  const [usersPages, setUsersPages] = useState(1)
  const [buildsPages, setBuildsPages] = useState(1)
  const [logsPages, setLogsPages] = useState(1)
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('')
  const debouncedSearchQuery = useDebounce(searchQuery, 300) // Debounce search
  const [buildStatusFilter, setBuildStatusFilter] = useState<string>('all')
  const [logLevelFilter, setLogLevelFilter] = useState<string>('all')
  const [logCategoryFilter, setLogCategoryFilter] = useState<string>('all')
  const [activeTab, setActiveTab] = useState<string>('dashboard')
  
  // Templates state
  const [templates, setTemplates] = useState<any[]>([])
  const [availableFeatures, setAvailableFeatures] = useState<any[]>([])
  const [showCreateTemplate, setShowCreateTemplate] = useState(false)
  const [showEditTemplate, setShowEditTemplate] = useState<any | null>(null)
  const [showViewTemplate, setShowViewTemplate] = useState<any | null>(null)
  const [newTemplateData, setNewTemplateData] = useState({
    id: '',
    name: '',
    description: '',
    features: [] as string[],
    recommended: false,
    icon: 'globe',
    color: 'primary'
  })
  
  // Handle filter changes
  const handleBuildStatusFilterChange = (value: string) => {
    setBuildStatusFilter(value)
    setBuildsPage(1) // Reset to first page
  }
  
  const handleLogLevelFilterChange = (value: string) => {
    setLogLevelFilter(value)
    setLogsPage(1) // Reset to first page
  }
  
  const handleLogCategoryFilterChange = (value: string) => {
    setLogCategoryFilter(value)
    setLogsPage(1) // Reset to first page
  }

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/admin/login')
    }
  }, [user, authLoading, router])
  
  // Séparer la vérification admin dans un useEffect pour éviter le warning React
  useEffect(() => {
    if (!authLoading && user && user.role !== 'admin') {
      toast.error('Admin access required')
      router.push('/dashboard')
    }
  }, [user, authLoading, router])

  const fetchAdminData = useCallback(async () => {
    if (!user?.id) {
      logger.warn('No user ID available', { context: 'fetchAdminData' })
      return
    }
    
    // Ne plus faire router.push ici pour éviter le warning React
    if (user.role !== 'admin') {
      logger.warn('User is not admin, skipping fetch', { userId: user.id, role: user.role })
      return
    }

    try {
      // Fonction helper pour retry avec timeout augmenté
      const fetchWithRetry = async <T,>(
        fetchFn: () => Promise<T>,
        retries: number = 2,
        delay: number = 1000
      ): Promise<T> => {
        for (let i = 0; i < retries; i++) {
          try {
            return await fetchFn();
          } catch (error: any) {
            const isLastAttempt = i === retries - 1;
            const isTimeout = error.code === 'ECONABORTED' || error.message?.includes('timeout');
            
            if (isLastAttempt || !isTimeout) {
              throw error;
            }
            
            logger.warn(`Retry ${i + 1}/${retries} after ${delay}ms`, { retry: i + 1, totalRetries: retries, delay })
            await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
          }
        }
        throw new Error('Max retries exceeded');
      };
      
      const [usersData, projectsData, buildsData, logsData, analyticsData, configData, templatesData, featuresData, visitStatsData] = await Promise.all([
        fetchWithRetry(() => adminApi.getUsers(usersPage, 20, true), 2, 1000),
        fetchWithRetry(() => adminApi.getProjects(projectsPage, 20), 2, 1000).catch(() => ({ projects: [], total: 0, pages: 1, page: 1 })),
        fetchWithRetry(() => adminApi.getBuilds(buildsPage, 20, buildStatusFilter !== 'all' ? buildStatusFilter : undefined), 2, 1000),
        fetchWithRetry(() => adminApi.getLogs(logsPage, 50, logLevelFilter !== 'all' ? logLevelFilter : undefined, logCategoryFilter !== 'all' ? logCategoryFilter : undefined), 2, 1000),
        fetchWithRetry(() => adminApi.getAnalytics(), 2, 1000),
        fetchWithRetry(() => adminApi.getConfig(), 2, 1000).catch(() => null),
        fetchWithRetry(() => adminApi.getTemplates(), 2, 1000).catch(() => ({ templates: [] })),
        fetchWithRetry(() => featuresApi.getAll(), 2, 1000).catch(() => []),
        fetchWithRetry(() => adminApi.getVisitStats(), 2, 1000).catch(() => null)
      ])
      
      setProjects(projectsData.projects || [])
      setProjectsTotal(projectsData.total || 0)
      setProjectsPages(projectsData.pages || 1)
      
      setUsers(usersData.users || [])
      setUsersTotal(usersData.total || 0)
      setUsersPages(usersData.pages || 1)
      
      setBuilds(buildsData.builds || [])
      setBuildsTotal(buildsData.total || 0)
      setBuildsPages(buildsData.pages || 1)
      
      setLogs(logsData.logs || [])
      setLogsTotal(logsData.total || 0)
      setLogsPages(logsData.pages || 1)
      
      setAnalytics(analyticsData)
      if (configData) setConfig(configData)
      if (templatesData?.templates) setTemplates(templatesData.templates)
      if (visitStatsData) setVisitStats(visitStatsData)
      
      // Load available features for template creation
      if (Array.isArray(featuresData) && featuresData.length > 0) {
        setAvailableFeatures(featuresData)
      } else {
        // Default features if API fails
        setAvailableFeatures([
          { id: 'push_notifications', name: 'Push Notifications' },
          { id: 'local_storage', name: 'Local Storage' },
          { id: 'geolocation', name: 'Géolocalisation' },
          { id: 'camera', name: 'Caméra' },
          { id: 'biometrics', name: 'Biométrie' },
          { id: 'share', name: 'Partage' },
          { id: 'clipboard', name: 'Presse-papiers' },
          { id: 'contacts', name: 'Contacts' },
          { id: 'file_system', name: 'Système de fichiers' },
          { id: 'haptics', name: 'Feedback haptique' },
          { id: 'deep_links', name: 'Deep Links' },
          { id: 'app_badge', name: 'Badge d\'application' },
        ])
      }
      if (templatesData?.templates) setTemplates(templatesData.templates)
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Admin access required')
        router.push('/dashboard')
      } else {
        logger.error('Failed to fetch admin data', error, {
          response: error.response?.data,
          status: error.response?.status,
          url: error.config?.url
        })
        
        // Afficher un message plus détaillé
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to load admin data'
        toast.error(errorMessage, { duration: 5000 })
        
        // Afficher les données partielles si disponibles
        if (error.response?.data) {
          logger.info('Partial data received', { data: error.response.data })
        }
      }
    } finally {
      setLoading(false)
    }
  }, [user, router, usersPage, projectsPage, buildsPage, logsPage, buildStatusFilter, logLevelFilter, logCategoryFilter, debouncedSearchQuery])

  useEffect(() => {
    if (user?.id && user?.role === 'admin') {
      setLoading(true)
      fetchAdminData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchAdminData])
  
  const handleRefresh = useCallback(() => {
    setLoading(true)
    fetchAdminData().then(() => {
      toast.success('Données actualisées')
    }).catch(() => {
      toast.error('Erreur lors de l\'actualisation')
    })
  }, [fetchAdminData])

  const handleBanUser = async (userId: string) => {
    if (!user?.id) return
    try {
      await adminApi.updateUser(userId, { status: 'banned' })
      toast.success('Utilisateur banni')
      // Recharger les données pour avoir les statistiques à jour
      await fetchAdminData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors du bannissement')
    }
  }

  const handleUnbanUser = async (userId: string) => {
    if (!user?.id) return
    try {
      await adminApi.updateUser(userId, { status: 'active' })
      toast.success('Utilisateur débanni')
      // Recharger les données pour avoir les statistiques à jour
      await fetchAdminData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors du débannissement')
    }
  }

  const handleCreateUser = async () => {
    if (!newUserData.email || !newUserData.password || !newUserData.name) {
      toast.error('Veuillez remplir tous les champs')
      return
    }
    if (newUserData.password.length < 6) {
      toast.error('Le mot de passe doit contenir au moins 6 caractères')
      return
    }
    try {
      await adminApi.createUser(newUserData)
      toast.success('Utilisateur créé avec succès')
      setShowCreateUser(false)
      setNewUserData({ email: '', password: '', name: '', role: 'user' })
      // Recharger les données
      await fetchAdminData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la création de l\'utilisateur')
      logger.error('Error creating user', error, { userData: newUserData })
    }
  }

  const handleEditUser = async (userId: string, updates: { role?: string; status?: string }) => {
    try {
      await adminApi.updateUser(userId, updates)
      // Mettre à jour l'utilisateur dans la liste locale
      const updatedUser = users.find(u => u.id === userId)
      if (updatedUser) {
        setShowEditUser({ ...updatedUser, ...updates })
        setUsers(users.map(u => u.id === userId ? { ...u, ...updates } : u))
      }
      toast.success('Utilisateur mis à jour avec succès')
      // Recharger les données pour avoir les statistiques à jour
      await fetchAdminData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la mise à jour de l\'utilisateur')
      logger.error('Error updating user', error, { userId, updates })
    }
  }

  const handleDeleteUser = async (userId: string) => {
    const userToDelete = users.find(u => u.id === userId)
    if (!confirm(`Êtes-vous sûr de vouloir supprimer l'utilisateur "${userToDelete?.email}" ? Cette action est irréversible.`)) return
    try {
      await adminApi.deleteUser(userId)
      toast.success('Utilisateur supprimé avec succès')
      // Recharger les données
      await fetchAdminData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la suppression de l\'utilisateur')
      logger.error('Error deleting user', error, { userId })
    }
  }

  const handleDeleteProject = async (projectId: string) => {
    const projectToDelete = projects.find(p => p.id === projectId)
    if (!confirm(`Êtes-vous sûr de vouloir supprimer le projet "${projectToDelete?.name}" ? Cette action est irréversible.`)) return
    try {
      await adminApi.deleteProject(projectId)
      toast.success('Projet supprimé avec succès')
      // Recharger les données
      await fetchAdminData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la suppression du projet')
      logger.error('Error deleting project', error, { projectId })
    }
  }
  
  const handleCreateTemplate = async () => {
    if (!newTemplateData.id || !newTemplateData.name) {
      toast.error('Veuillez remplir au moins l\'ID et le nom du template')
      return
    }
    try {
      await adminApi.createTemplate({
        id: newTemplateData.id,
        name: newTemplateData.name,
        description: newTemplateData.description || '',
        features: newTemplateData.features || [],
        recommended: newTemplateData.recommended || false,
        icon: newTemplateData.icon || 'globe',
        color: newTemplateData.color || 'primary'
      })
      toast.success('Template créé avec succès')
      setShowCreateTemplate(false)
      setNewTemplateData({
        id: '',
        name: '',
        description: '',
        features: [],
        recommended: false,
        icon: 'globe',
        color: 'primary'
      })
      // Recharger les données
      await fetchAdminData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la création du template')
      logger.error('Error creating template', error, { templateData: newTemplateData })
    }
  }

  const handleUpdateTemplate = async (templateId: string, updates: any) => {
    try {
      await adminApi.updateTemplate(templateId, updates)
      toast.success('Template mis à jour avec succès')
      setShowEditTemplate(null)
      // Recharger les données
      await fetchAdminData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la mise à jour du template')
      logger.error('Error updating template', error, { templateId, updates })
    }
  }

  const handleDeleteTemplate = async (templateId: string) => {
    const templateToDelete = templates.find(t => t.id === templateId)
    if (!confirm(`Êtes-vous sûr de vouloir supprimer le template "${templateToDelete?.name}" ? Cette action est irréversible.`)) return
    try {
      await adminApi.deleteTemplate(templateId)
      toast.success('Template supprimé avec succès')
      // Recharger les données
      await fetchAdminData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la suppression du template')
      logger.error('Error deleting template', error, { templateId })
    }
  }

  const handleUpdateConfig = async (updates: Partial<PlatformConfig>) => {
    if (!user?.id || !config) return
    try {
      const updatedConfig = { ...config, ...updates }
      // Validation
      if (updatedConfig.max_builds_per_user < 1 || updatedConfig.max_builds_per_user > 1000) {
        toast.error('Le nombre maximum de builds doit être entre 1 et 1000')
        return
      }
      if (updatedConfig.max_projects_per_user < 1 || updatedConfig.max_projects_per_user > 100) {
        toast.error('Le nombre maximum de projets doit être entre 1 et 100')
        return
      }
      if (updatedConfig.build_timeout_minutes < 1 || updatedConfig.build_timeout_minutes > 120) {
        toast.error('Le délai d\'expiration doit être entre 1 et 120 minutes')
        return
      }
      
      const savedConfig = await adminApi.updateConfig(updatedConfig)
      setConfig(savedConfig || updatedConfig)
      toast.success('Configuration mise à jour avec succès')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la mise à jour de la configuration')
      logger.error('Error updating config', error, { config })
    }
  }
  
  // Memoized filtered results for better performance
  const filteredUsers = useMemo(() => {
    if (!debouncedSearchQuery) return users
    const query = debouncedSearchQuery.toLowerCase()
    return users.filter(u => 
      u.name.toLowerCase().includes(query) ||
      u.email.toLowerCase().includes(query)
    )
  }, [users, debouncedSearchQuery])
  
  const filteredBuilds = useMemo(() => {
    if (!debouncedSearchQuery) return builds
    const query = debouncedSearchQuery.toLowerCase()
    return builds.filter(b =>
      b.project_name.toLowerCase().includes(query) ||
      b.user_name.toLowerCase().includes(query)
    )
  }, [builds, debouncedSearchQuery])
  
  const filteredLogs = useMemo(() => {
    if (!debouncedSearchQuery) return logs
    const query = debouncedSearchQuery.toLowerCase()
    return logs.filter(l =>
      l.message.toLowerCase().includes(query)
    )
  }, [logs, debouncedSearchQuery])

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  if (user.role !== 'admin') {
    // Rediriger vers la page de login admin si l'utilisateur n'est pas admin
    router.push('/admin/login?error=not_admin')
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Redirection...</p>
        </div>
      </div>
    )
  }

  return (
    <AdminLayout 
      title="Tableau de Bord Administrateur"
      activeTab={activeTab}
      onTabChange={setActiveTab}
    >
      {/* Header Actions */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Actualiser
          </Button>
        </div>
      </div>

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

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-background-subtle grid grid-cols-2 md:grid-cols-5 lg:grid-cols-10 w-full">
          <TabsTrigger value="dashboard">
            <BarChart3 className="w-4 h-4 mr-2" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="users">
            <Users className="w-4 h-4 mr-2" />
            Utilisateurs ({usersTotal})
          </TabsTrigger>
          <TabsTrigger value="projects">
            <FolderKanban className="w-4 h-4 mr-2" />
            Projets
          </TabsTrigger>
          <TabsTrigger value="builds">
            <Hammer className="w-4 h-4 mr-2" />
            Builds ({buildsTotal})
          </TabsTrigger>
          <TabsTrigger value="logs">
            <FileText className="w-4 h-4 mr-2" />
            Logs ({logsTotal})
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <TrendingUp className="w-4 h-4 mr-2" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="templates">
            <FileCode className="w-4 h-4 mr-2" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="api-keys">
            <Key className="w-4 h-4 mr-2" />
            API Keys
          </TabsTrigger>
          <TabsTrigger value="monitoring">
            <Activity className="w-4 h-4 mr-2" />
            Monitoring
          </TabsTrigger>
          <TabsTrigger value="config">
            <Settings className="w-4 h-4 mr-2" />
            Config
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          {/* Dashboard Overview - Analytics déjà affiché au-dessus */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="bg-background-paper border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Utilisateurs Actifs</p>
                    <p className="text-3xl font-bold">{analytics?.users.active || 0}</p>
                    <p className="text-xs text-muted-foreground">sur {analytics?.users.total || 0} total</p>
                  </div>
                  <Users className="w-8 h-8 text-primary" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-background-paper border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Taux de Réussite</p>
                    <p className="text-3xl font-bold">{analytics?.builds.success_rate || 0}%</p>
                    <p className="text-xs text-muted-foreground">{analytics?.builds.successful || 0} réussis</p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-success" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-background-paper border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Builds Échoués</p>
                    <p className="text-3xl font-bold">{analytics?.builds.failed || 0}</p>
                    <p className="text-xs text-muted-foreground">sur {analytics?.builds.total || 0} total</p>
                  </div>
                  <XCircle className="w-8 h-8 text-destructive" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-background-paper border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Alertes Système</p>
                    <p className="text-3xl font-bold">
                      {logs.filter(l => l.level === 'error').length}
                    </p>
                    <p className="text-xs text-muted-foreground">Erreurs récentes</p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-warning" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="users">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Gestion des Utilisateurs</CardTitle>
                  <CardDescription>Créer, modifier et gérer les utilisateurs de la plateforme</CardDescription>
                </div>
                <Button onClick={() => setShowCreateUser(true)}>
                  <UserPlus className="w-4 h-4 mr-2" />
                  Créer un utilisateur
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* Search and Filters */}
              <div className="mb-4 flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Rechercher un utilisateur..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              {/* Edit User Dialog */}
              {showEditUser && (
                <Card className="mb-4 border-primary/30 bg-primary/5">
                  <CardHeader>
                    <CardTitle>Modifier l&apos;utilisateur</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>Rôle</Label>
                      <Select 
                        value={showEditUser.role} 
                        onValueChange={(v) => {
                          setShowEditUser({ ...showEditUser, role: v })
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user">Utilisateur</SelectItem>
                          <SelectItem value="admin">Administrateur</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Statut</Label>
                      <Select 
                        value={showEditUser.status} 
                        onValueChange={(v) => {
                          setShowEditUser({ ...showEditUser, status: v })
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">Actif</SelectItem>
                          <SelectItem value="banned">Banni</SelectItem>
                          <SelectItem value="inactive">Inactif</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex gap-2 pt-2">
                      <Button onClick={() => {
                        if (showEditUser) {
                          handleEditUser(showEditUser.id, { 
                            role: showEditUser.role, 
                            status: showEditUser.status 
                          })
                        }
                      }}>
                        Enregistrer
                      </Button>
                      <Button variant="outline" onClick={() => setShowEditUser(null)}>
                        Annuler
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Create User Dialog */}
              {showCreateUser && (
                <Card className="mb-4 border-primary/30 bg-primary/5">
                  <CardHeader>
                    <CardTitle>Créer un nouvel utilisateur</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>Nom</Label>
                      <Input value={newUserData.name} onChange={(e) => setNewUserData({...newUserData, name: e.target.value})} />
                    </div>
                    <div>
                      <Label>Email</Label>
                      <Input type="email" value={newUserData.email} onChange={(e) => setNewUserData({...newUserData, email: e.target.value})} />
                    </div>
                    <div>
                      <Label>Mot de passe</Label>
                      <Input type="password" value={newUserData.password} onChange={(e) => setNewUserData({...newUserData, password: e.target.value})} />
                    </div>
                    <div>
                      <Label>Rôle</Label>
                      <Select value={newUserData.role} onValueChange={(v) => setNewUserData({...newUserData, role: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user">Utilisateur</SelectItem>
                          <SelectItem value="admin">Administrateur</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex gap-2">
                      <Button onClick={handleCreateUser}>Créer</Button>
                      <Button variant="outline" onClick={() => setShowCreateUser(false)}>Annuler</Button>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {loading ? (
                <div className="flex justify-center py-10">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : (
                <>
                  <ScrollArea className="h-[500px]">
                    <div className="space-y-3">
                      {filteredUsers.length === 0 ? (
                        <div className="text-center py-10 text-muted-foreground">
                          Aucun utilisateur trouvé
                        </div>
                      ) : (
                        filteredUsers.map((u) => (
                          <div key={u.id} className="flex items-center justify-between p-4 rounded-lg border border-white/10">
                            <div>
                              <p className="font-medium">{u.name}</p>
                              <p className="text-sm text-muted-foreground">{u.email}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge variant={u.role === 'admin' ? 'default' : 'outline'}>
                                  {u.role}
                                </Badge>
                                <Badge variant={u.status === 'active' ? 'default' : 'destructive'}>
                                  {u.status}
                                </Badge>
                              </div>
                              <p className="text-xs text-muted-foreground mt-1">
                                {u.projects_count} projects • {u.builds_count} builds
                              </p>
                            </div>
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setShowEditUser(u)}
                              >
                                <Edit className="w-4 h-4 mr-1" />
                                Modifier
                              </Button>
                              {u.status === 'active' ? (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="border-destructive/30 text-destructive hover:bg-destructive/10"
                                  onClick={() => handleBanUser(u.id)}
                                  disabled={u.role === 'admin' || u.id === user?.id}
                                >
                                  <Ban className="w-4 h-4 mr-1" />
                                  Bannir
                                </Button>
                              ) : (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="border-success/30 text-success hover:bg-success/10"
                                  onClick={() => handleUnbanUser(u.id)}
                                >
                                  <CheckCircle2 className="w-4 h-4 mr-1" />
                                  Débannir
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                className="border-destructive/30 text-destructive hover:bg-destructive/10"
                                onClick={() => handleDeleteUser(u.id)}
                                disabled={u.id === user?.id}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                  
                  {/* Pagination */}
                  {usersPages > 1 && (
                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/10">
                      <p className="text-sm text-muted-foreground">
                        Page {usersPage} sur {usersPages} • {usersTotal} utilisateurs au total
                      </p>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setUsersPage(p => Math.max(1, p - 1))}
                          disabled={usersPage === 1}
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setUsersPage(p => Math.min(usersPages, p + 1))}
                          disabled={usersPage === usersPages}
                        >
                          <ChevronRight className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="builds">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>Historique des Builds</CardTitle>
              <CardDescription>Tous les builds de la plateforme</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              <div className="mb-4 flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Rechercher un build..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={buildStatusFilter} onValueChange={handleBuildStatusFilterChange}>
                  <SelectTrigger className="w-[180px]">
                    <Filter className="w-4 h-4 mr-2" />
                    <SelectValue placeholder="Statut" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tous les statuts</SelectItem>
                    <SelectItem value="pending">En attente</SelectItem>
                    <SelectItem value="processing">En cours</SelectItem>
                    <SelectItem value="completed">Terminé</SelectItem>
                    <SelectItem value="failed">Échoué</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <ScrollArea className="h-[500px]">
                <div className="space-y-3">
                  {filteredBuilds.length === 0 ? (
                    <div className="text-center py-10 text-muted-foreground">
                      Aucun build trouvé
                    </div>
                  ) : (
                    filteredBuilds.map((build) => (
                      <div key={build.id} className="flex items-center justify-between p-4 rounded-lg border border-white/10">
                        <div>
                          <p className="font-medium">{build.project_name}</p>
                          <p className="text-sm text-muted-foreground">by {build.user_name}</p>
                          <p className="text-xs text-muted-foreground">{new Date(build.created_at).toLocaleString()}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{build.platform}</Badge>
                          <Badge variant={build.status === 'completed' ? 'default' : build.status === 'failed' ? 'destructive' : 'outline'}>
                            {build.status}
                          </Badge>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
              
              {/* Pagination */}
              {buildsPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/10">
                  <p className="text-sm text-muted-foreground">
                    Page {buildsPage} sur {buildsPages} • {buildsTotal} builds au total
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setBuildsPage(p => Math.max(1, p - 1))}
                      disabled={buildsPage === 1}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setBuildsPage(p => Math.min(buildsPages, p + 1))}
                      disabled={buildsPage === buildsPages}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>Logs Système</CardTitle>
              <CardDescription>Journal d'activité de la plateforme</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              <div className="mb-4 flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Rechercher dans les logs..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={logLevelFilter} onValueChange={handleLogLevelFilterChange}>
                  <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="Niveau" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tous les niveaux</SelectItem>
                    <SelectItem value="info">Info</SelectItem>
                    <SelectItem value="warning">Warning</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={logCategoryFilter} onValueChange={handleLogCategoryFilterChange}>
                  <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="Catégorie" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes les catégories</SelectItem>
                    <SelectItem value="auth">Auth</SelectItem>
                    <SelectItem value="project">Project</SelectItem>
                    <SelectItem value="build">Build</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <ScrollArea className="h-[500px]">
                <div className="space-y-2">
                  {filteredLogs.length === 0 ? (
                    <div className="text-center py-10 text-muted-foreground">
                      Aucun log trouvé
                    </div>
                  ) : (
                    filteredLogs.map((log) => (
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
                    ))
                  )}
                </div>
              </ScrollArea>
              
              {/* Pagination */}
              {logsPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/10">
                  <p className="text-sm text-muted-foreground">
                    Page {logsPage} sur {logsPages} • {logsTotal} logs au total
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setLogsPage(p => Math.max(1, p - 1))}
                      disabled={logsPage === 1}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setLogsPage(p => Math.min(logsPages, p + 1))}
                      disabled={logsPage === logsPages}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="projects">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>Gestion de TOUS les Projets</CardTitle>
              <CardDescription>Tous les projets de tous les utilisateurs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 flex items-center gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Rechercher un projet..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              <ScrollArea className="h-[500px]">
                <div className="space-y-3">
                  {projects.length === 0 ? (
                    <div className="text-center py-10 text-muted-foreground">
                      Aucun projet trouvé
                    </div>
                  ) : (
                    projects.map((project) => (
                      <div key={project.id} className="flex items-center justify-between p-4 rounded-lg border border-white/10">
                        <div className="flex-1">
                          <p className="font-medium">{project.name}</p>
                          <p className="text-sm text-muted-foreground">{project.web_url}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="outline">{project.user_email}</Badge>
                            {project.platform?.map((p: string) => (
                              <Badge key={p} variant="outline">{p}</Badge>
                            ))}
                          <Badge variant={project.status === 'active' ? 'default' : 'outline'}>
                            {project.status}
                          </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            {project.builds_count || 0} builds • Créé le {new Date(project.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => router.push(`/projects/${project.id}`)}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            Voir
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-destructive/30 text-destructive hover:bg-destructive/10"
                            onClick={() => handleDeleteProject(project.id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
              
              {projectsPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/10">
                  <p className="text-sm text-muted-foreground">
                    Page {projectsPage} sur {projectsPages} • {projectsTotal} projets au total
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setProjectsPage(p => Math.max(1, p - 1))}
                      disabled={projectsPage === 1}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setProjectsPage(p => Math.min(projectsPages, p + 1))}
                      disabled={projectsPage === projectsPages}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="config">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>Configuration de la Plateforme</CardTitle>
              <CardDescription>Paramètres globaux de NativiWeb Studio</CardDescription>
            </CardHeader>
            <CardContent>
              {config ? (
                <div className="space-y-6">
                  <div className="flex items-center justify-between p-4 rounded-lg border border-white/10">
                    <div className="space-y-0.5">
                      <Label htmlFor="maintenance-mode" className="text-base">
                        Mode Maintenance
                      </Label>
                      <p className="text-sm text-muted-foreground">
                        Désactive l'accès à la plateforme pour tous les utilisateurs sauf les admins
                      </p>
                    </div>
                    <Switch
                      id="maintenance-mode"
                      checked={config.maintenance_mode}
                      onCheckedChange={(checked) => handleUpdateConfig({ maintenance_mode: checked })}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="max-builds">Nombre maximum de builds par utilisateur</Label>
                    <Input
                      id="max-builds"
                      type="number"
                      value={config.max_builds_per_user}
                      onChange={(e) => handleUpdateConfig({ max_builds_per_user: parseInt(e.target.value) })}
                      min={1}
                      max={1000}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="max-projects">Nombre maximum de projets par utilisateur</Label>
                    <Input
                      id="max-projects"
                      type="number"
                      value={config.max_projects_per_user}
                      onChange={(e) => handleUpdateConfig({ max_projects_per_user: parseInt(e.target.value) })}
                      min={1}
                      max={100}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="build-timeout">Délai d'expiration des builds (minutes)</Label>
                    <Input
                      id="build-timeout"
                      type="number"
                      value={config.build_timeout_minutes}
                      onChange={(e) => handleUpdateConfig({ build_timeout_minutes: parseInt(e.target.value) })}
                      min={1}
                      max={120}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="allowed-domains">Domaines autorisés (un par ligne)</Label>
                    <textarea
                      id="allowed-domains"
                      className="w-full min-h-[100px] p-3 rounded-md bg-background border border-white/10 text-foreground"
                      value={config.allowed_domains?.join('\n') || ''}
                      onChange={(e) => {
                        const domains = e.target.value.split('\n').filter(d => d.trim())
                        handleUpdateConfig({ allowed_domains: domains })
                      }}
                      placeholder="example.com&#10;app.example.com"
                    />
                    <p className="text-sm text-muted-foreground">
                      Liste des domaines autorisés pour les projets (laisser vide pour autoriser tous les domaines)
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-10">
                  <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
                  <p className="text-muted-foreground">Chargement de la configuration...</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle>Statistiques Utilisateurs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Utilisateurs</span>
                    <span className="font-bold">{analytics?.users.total || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Utilisateurs Actifs</span>
                    <span className="font-bold text-green-500">{analytics?.users.active || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Utilisateurs Bannis</span>
                    <span className="font-bold text-destructive">
                      {(analytics?.users.total || 0) - (analytics?.users.active || 0)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle>Statistiques Builds</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Builds</span>
                    <span className="font-bold">{analytics?.builds.total || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Réussis</span>
                    <span className="font-bold text-green-500">{analytics?.builds.successful || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Échoués</span>
                    <span className="font-bold text-destructive">{analytics?.builds.failed || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Taux de Réussite</span>
                    <span className="font-bold">{analytics?.builds.success_rate || 0}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle>Répartition par Plateforme</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Android</span>
                    <span className="font-bold">{analytics?.platforms.android || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>iOS</span>
                    <span className="font-bold">{analytics?.platforms.ios || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle>Projets</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Projets</span>
                    <span className="font-bold text-2xl">{analytics?.projects.total || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Statistiques de Visites */}
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="w-5 h-5 text-primary" />
                    Visites du Site
                  </CardTitle>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => fetchAdminData()}
                  >
                    <RefreshCw className="w-4 h-4 mr-1" />
                    Actualiser
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {visitStats ? (
                  <div className="space-y-6">
                    {/* Statistiques principales */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                        <div className="flex items-center gap-2 mb-2">
                          <TrendingUp className="w-4 h-4 text-primary" />
                          <span className="text-sm text-muted-foreground">Total Visites</span>
                        </div>
                        <p className="text-3xl font-bold">{visitStats.total_visits.toLocaleString()}</p>
                      </div>
                      <div className="p-4 rounded-lg bg-success/5 border border-success/20">
                        <div className="flex items-center gap-2 mb-2">
                          <Users className="w-4 h-4 text-success" />
                          <span className="text-sm text-muted-foreground">Visiteurs Uniques</span>
                        </div>
                        <p className="text-3xl font-bold">{visitStats.unique_visitors.toLocaleString()}</p>
                      </div>
                    </div>

                    {/* Visites par période */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-3 rounded-lg bg-background/50 border border-white/10">
                        <p className="text-xs text-muted-foreground mb-1">Aujourd'hui</p>
                        <p className="text-xl font-bold">{visitStats.visits_today}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-background/50 border border-white/10">
                        <p className="text-xs text-muted-foreground mb-1">Cette Semaine</p>
                        <p className="text-xl font-bold">{visitStats.visits_this_week}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-background/50 border border-white/10">
                        <p className="text-xs text-muted-foreground mb-1">Ce Mois</p>
                        <p className="text-xl font-bold">{visitStats.visits_this_month}</p>
                      </div>
                    </div>

                    {/* Top pages */}
                    {visitStats.top_pages && visitStats.top_pages.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-3">Pages les Plus Visitées</h4>
                        <div className="space-y-2">
                          {visitStats.top_pages.slice(0, 5).map((page, index) => (
                            <div key={index} className="flex items-center justify-between p-2 rounded bg-background/50 border border-white/10">
                              <span className="text-sm font-mono text-muted-foreground truncate flex-1">{page.path}</span>
                              <Badge variant="outline" className="ml-2">{page.count}</Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Répartition par appareil */}
                    {visitStats.device_breakdown && Object.keys(visitStats.device_breakdown).length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-3">Répartition par Appareil</h4>
                        <div className="space-y-2">
                          {Object.entries(visitStats.device_breakdown).map(([device, count]) => (
                            <div key={device} className="flex items-center justify-between">
                              <span className="text-sm capitalize">{device === 'unknown' ? 'Non défini' : device}</span>
                              <div className="flex items-center gap-2">
                                <div className="w-24 h-2 bg-background rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-primary"
                                    style={{ 
                                      width: `${visitStats.total_visits > 0 ? (count / visitStats.total_visits * 100) : 0}%` 
                                    }}
                                  />
                                </div>
                                <span className="text-sm font-medium w-12 text-right">{count}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-10">
                    <Globe className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">Aucune statistique de visite disponible</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Les statistiques apparaîtront une fois que les visites commenceront à être trackées
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="templates">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Gestion des Templates</CardTitle>
                  <CardDescription>Créer, modifier et gérer les templates de projets disponibles</CardDescription>
                </div>
                <Button onClick={() => setShowCreateTemplate(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Ajouter un template
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* Create Template Dialog */}
              {showCreateTemplate && (
                <Card className="mb-4 border-primary/30 bg-primary/5">
                  <CardHeader>
                    <CardTitle>Créer un nouveau template</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>ID (unique, en minuscules, sans espaces)</Label>
                      <Input 
                        value={newTemplateData.id} 
                        onChange={(e) => setNewTemplateData({...newTemplateData, id: e.target.value.toLowerCase().replace(/\s+/g, '-')})}
                        placeholder="ex: my-custom-template"
                      />
                    </div>
                    <div>
                      <Label>Nom</Label>
                      <Input 
                        value={newTemplateData.name} 
                        onChange={(e) => setNewTemplateData({...newTemplateData, name: e.target.value})}
                        placeholder="Ex: Template E-Commerce"
                      />
                    </div>
                    <div>
                      <Label>Description</Label>
                      <textarea
                        className="w-full min-h-[80px] p-3 rounded-md bg-background border border-white/10 text-foreground"
                        value={newTemplateData.description}
                        onChange={(e) => setNewTemplateData({...newTemplateData, description: e.target.value})}
                        placeholder="Description du template..."
                      />
                    </div>
                    <div>
                      <Label>Fonctionnalités</Label>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2 max-h-40 overflow-y-auto p-2 border border-white/10 rounded-md">
                        {availableFeatures.map((feature) => (
                          <div key={feature.id || feature} className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id={`feature-${feature.id || feature}`}
                              checked={newTemplateData.features.includes(feature.id || feature)}
                              onChange={(e) => {
                                const featureId = feature.id || feature
                                if (e.target.checked) {
                                  setNewTemplateData({
                                    ...newTemplateData,
                                    features: [...newTemplateData.features, featureId]
                                  })
                                } else {
                                  setNewTemplateData({
                                    ...newTemplateData,
                                    features: newTemplateData.features.filter(f => f !== featureId)
                                  })
                                }
                              }}
                              className="rounded border-white/20"
                            />
                            <Label 
                              htmlFor={`feature-${feature.id || feature}`}
                              className="text-sm cursor-pointer"
                            >
                              {feature.name || feature}
                            </Label>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <Label>Couleur</Label>
                      <Select value={newTemplateData.color} onValueChange={(v) => setNewTemplateData({...newTemplateData, color: v})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="primary">Primary</SelectItem>
                          <SelectItem value="secondary">Secondary</SelectItem>
                          <SelectItem value="success">Success</SelectItem>
                          <SelectItem value="warning">Warning</SelectItem>
                          <SelectItem value="destructive">Destructive</SelectItem>
                          <SelectItem value="info">Info</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="recommended"
                        checked={newTemplateData.recommended}
                        onCheckedChange={(checked) => setNewTemplateData({...newTemplateData, recommended: checked})}
                      />
                      <Label htmlFor="recommended">Template recommandé</Label>
                    </div>
                    <div className="flex gap-2">
                      <Button onClick={handleCreateTemplate}>Créer</Button>
                      <Button variant="outline" onClick={() => setShowCreateTemplate(false)}>Annuler</Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* View Template Dialog */}
              {showViewTemplate && (
                <Card className="mb-4 border-primary/30 bg-primary/5">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>Détails du Template</CardTitle>
                      <Button variant="ghost" size="icon" onClick={() => setShowViewTemplate(null)}>
                        <XCircle className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>ID</Label>
                      <p className="text-sm text-muted-foreground">{showViewTemplate.id}</p>
                    </div>
                    <div>
                      <Label>Nom</Label>
                      <p className="text-sm font-medium">{showViewTemplate.name}</p>
                    </div>
                    <div>
                      <Label>Description</Label>
                      <p className="text-sm text-muted-foreground">{showViewTemplate.description}</p>
                    </div>
                    <div>
                      <Label>Fonctionnalités</Label>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {showViewTemplate.features && showViewTemplate.features.length > 0 ? (
                          showViewTemplate.features.map((feature: string) => (
                            <Badge key={feature} variant="outline">{feature}</Badge>
                          ))
                        ) : (
                          <span className="text-sm text-muted-foreground">Aucune fonctionnalité</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Label>Recommandé:</Label>
                      <Badge variant={showViewTemplate.recommended ? 'default' : 'outline'}>
                        {showViewTemplate.recommended ? 'Oui' : 'Non'}
                      </Badge>
                    </div>
                    <Button variant="outline" onClick={() => setShowViewTemplate(null)}>Fermer</Button>
                  </CardContent>
                </Card>
              )}

              {/* Edit Template Dialog */}
              {showEditTemplate && (
                <Card className="mb-4 border-primary/30 bg-primary/5">
                  <CardHeader>
                    <CardTitle>Modifier le template</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>Nom</Label>
                      <Input 
                        value={showEditTemplate.name} 
                        onChange={(e) => setShowEditTemplate({...showEditTemplate, name: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label>Description</Label>
                      <textarea
                        className="w-full min-h-[80px] p-3 rounded-md bg-background border border-white/10 text-foreground"
                        value={showEditTemplate.description}
                        onChange={(e) => setShowEditTemplate({...showEditTemplate, description: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label>Couleur</Label>
                      <Select 
                        value={showEditTemplate.color} 
                        onValueChange={(v) => setShowEditTemplate({...showEditTemplate, color: v})}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="primary">Primary</SelectItem>
                          <SelectItem value="secondary">Secondary</SelectItem>
                          <SelectItem value="success">Success</SelectItem>
                          <SelectItem value="warning">Warning</SelectItem>
                          <SelectItem value="destructive">Destructive</SelectItem>
                          <SelectItem value="info">Info</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="edit-recommended"
                        checked={showEditTemplate.recommended}
                        onCheckedChange={(checked) => setShowEditTemplate({...showEditTemplate, recommended: checked})}
                      />
                      <Label htmlFor="edit-recommended">Template recommandé</Label>
                    </div>
                    <div className="flex gap-2">
                      <Button onClick={() => {
                        if (showEditTemplate) {
                          handleUpdateTemplate(showEditTemplate.id, {
                            name: showEditTemplate.name,
                            description: showEditTemplate.description,
                            color: showEditTemplate.color,
                            recommended: showEditTemplate.recommended
                          })
                        }
                      }}>
                        Enregistrer
                      </Button>
                      <Button variant="outline" onClick={() => setShowEditTemplate(null)}>Annuler</Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Templates List */}
              {loading ? (
                <div className="flex justify-center py-10">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {templates.length === 0 ? (
                    <div className="col-span-full text-center py-10 text-muted-foreground">
                      Aucun template trouvé. Créez votre premier template !
                    </div>
                  ) : (
                    templates.map((template) => (
                      <Card key={template.id} className="border-white/10 hover:border-primary/50 transition-colors">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <CardTitle className="text-lg">{template.name}</CardTitle>
                              <CardDescription>{template.description}</CardDescription>
                            </div>
                            {template.recommended && (
                              <Badge variant="default" className="ml-2">Recommandé</Badge>
                            )}
                          </div>
                          {template.features && template.features.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {template.features.slice(0, 3).map((feature: string) => (
                                <Badge key={feature} variant="outline" className="text-xs">{feature}</Badge>
                              ))}
                              {template.features.length > 3 && (
                                <Badge variant="outline" className="text-xs">+{template.features.length - 3}</Badge>
                              )}
                            </div>
                          )}
                        </CardHeader>
                        <CardContent>
                          <div className="flex gap-2">
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="flex-1"
                              onClick={() => setShowViewTemplate(template)}
                            >
                              <Eye className="w-4 h-4 mr-1" />
                              Voir
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => setShowEditTemplate({...template})}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="text-destructive hover:text-destructive"
                              onClick={() => handleDeleteTemplate(template.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api-keys">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>API Keys Globales</CardTitle>
                  <CardDescription>Gérer les clés API système et administrateur</CardDescription>
                </div>
                <Button onClick={() => toast.info('La création d\'API Keys globales sera disponible dans une prochaine version')}>
                  <Plus className="w-4 h-4 mr-2" />
                  Créer une clé API
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-sm text-muted-foreground mb-4">
                  Les API Keys globales permettent d&apos;accéder aux fonctionnalités administratives via l&apos;API.
                </div>
                <div className="text-center py-10 text-muted-foreground border border-white/10 rounded-lg">
                  <Key className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="font-medium mb-2">Aucune clé API globale</p>
                  <p className="text-sm">Créez votre première clé API pour commencer</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitoring">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle>Statut Système</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>API Backend</span>
                    <Badge variant="default" className="bg-green-500/20 text-green-500 border-green-500/30">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      En ligne
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Base de données</span>
                    <Badge variant="default" className="bg-green-500/20 text-green-500 border-green-500/30">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Connectée
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Stockage</span>
                    <Badge variant="default" className="bg-green-500/20 text-green-500 border-green-500/30">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Disponible
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle>Alertes Récentes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {logs.filter(l => l.level === 'error' || l.level === 'warning').slice(0, 5).map((log) => (
                    <div key={log.id} className="p-2 rounded border border-white/10 text-sm">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={log.level === 'error' ? 'destructive' : 'default'} className="text-xs">
                          {log.level}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-muted-foreground">{log.message}</p>
                    </div>
                  ))}
                  {logs.filter(l => l.level === 'error' || l.level === 'warning').length === 0 && (
                    <p className="text-center text-muted-foreground py-4">Aucune alerte récente</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </AdminLayout>
  )
}
