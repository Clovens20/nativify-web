'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { projectsApi, buildsApi, featuresApi } from '@/lib/api'
import { getBuildBackendConfig, getBuildBackendUrl } from '@/lib/buildBackend'
import { toast } from 'sonner'
import { logger } from '@/lib/logger'
import { useDownload } from '@/hooks/useDownload'
import { 
  Globe, 
  Smartphone, 
  Apple, 
  Play,
  Download,
  Settings,
  Loader2,
  Clock,
  CheckCircle2,
  Rocket,
  XCircle,
  AlertCircle,
  Trash2,
  Monitor,
  Palette,
  Image as ImageIcon
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface Feature {
  id: string
  name: string
  enabled: boolean
  config: Record<string, any>
}

interface Project {
  id: string
  name: string
  web_url: string
  description: string
  platform: string[]
  features: Feature[]
  status: string
  created_at: string
}

interface Build {
  id: string
  platform: string
  status: string
  phase: string
  progress: number
  logs: Array<{ level: string; message: string; timestamp: string }>
  artifacts: Array<{ name: string; type: string; size: string }>
  created_at: string
  completed_at: string | null
  duration_seconds: number | null
}

interface DependenciesStatus {
  ready: boolean
  errors: string[]
}

export default function ProjectDetailPage() {
  const { user, session } = useAuth()
  const router = useRouter()
  const params = useParams()
  const projectId = params.id as string
  const { download, isDownloading, progress } = useDownload()
  const buildBackendConfig = getBuildBackendConfig()
  
  const [project, setProject] = useState<Project | null>(null)
  const [builds, setBuilds] = useState<Build[]>([])
  const [availableFeatures, setAvailableFeatures] = useState<Feature[]>([])
  const [loading, setLoading] = useState(true)
  const [buildingPlatform, setBuildingPlatform] = useState<string | null>(null)
  const [activeBuild, setActiveBuild] = useState<Build | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteBuildDialogOpen, setDeleteBuildDialogOpen] = useState(false)
  const [buildToDelete, setBuildToDelete] = useState<Build | null>(null)
  const [deleting, setDeleting] = useState(false)
  
  // Advanced configuration states
  const [orientation, setOrientation] = useState<'portrait' | 'landscape' | 'sensor'>('sensor')
  const [statusBarStyle, setStatusBarStyle] = useState<'light' | 'dark'>('dark')
  const [statusBarColor, setStatusBarColor] = useState('#000000')
  const [generatingScreenshots, setGeneratingScreenshots] = useState(false)
  
  // Charger les configs avancées depuis le projet
  useEffect(() => {
    if (project && (project as any).advanced_config) {
      const config = (project as any).advanced_config
      if (config.orientation) {
        setOrientation(config.orientation)
      }
      if (config.status_bar) {
        setStatusBarStyle(config.status_bar.style || 'dark')
        setStatusBarColor(config.status_bar.color || '#000000')
      }
    }
  }, [project])

  useEffect(() => {
    const fetchData = async () => {
      if (!user?.id || !projectId) return
      
      setLoading(true)
      let retries = 3
      let delay = 500
      
      while (retries > 0) {
        try {
          // Utiliser Promise.allSettled pour ne pas bloquer sur les erreurs
          const [projectResult, buildsResult, featuresResult] = await Promise.allSettled([
            projectsApi.getOne(projectId),
            buildsApi.getAll(projectId).catch(() => []), // Ne pas bloquer si les builds échouent
            featuresApi.getAll().catch(() => []) // Ne pas bloquer si les features échouent
          ])
          
          // Traiter les résultats
          if (projectResult.status === 'fulfilled') {
            setProject(projectResult.value)
          } else {
            throw projectResult.reason
          }
          
          if (buildsResult.status === 'fulfilled') {
            setBuilds(buildsResult.value || [])
          }
          
          if (featuresResult.status === 'fulfilled') {
            setAvailableFeatures(featuresResult.value || [])
          }
          
          setLoading(false)
          return // Succès, sortir de la boucle
        } catch (error: any) {
          retries--
          const isNotFound = error.response?.status === 404
          const isConnectionError = error.isConnectionError || error.code === 'ECONNREFUSED' || error.message?.includes('Network Error')
          const isTimeout = error.code === 'ECONNABORTED' || error.message?.includes('timeout')
          
          if (isConnectionError) {
            // Erreur de connexion, ne pas réessayer indéfiniment
            logger.error('Backend connection error', error, { projectId, retries })
            if (retries === 0) {
              toast.error('Impossible de se connecter au serveur. Vérifiez que le backend est démarré.')
              setLoading(false)
              router.push('/projects')
            }
            return
          }
          
          if (isTimeout && retries > 0) {
            // Timeout, réessayer avec backoff exponentiel
            logger.warn('Request timeout - retrying', { retries, delay, projectId })
            await new Promise(resolve => setTimeout(resolve, delay))
            delay *= 2 // Backoff exponentiel
            continue
          }
          
          if (isNotFound && retries > 0) {
            // Projet pas encore disponible, réessayer après un délai
            logger.warn('Project not found - retrying', { retries, delay, projectId })
            await new Promise(resolve => setTimeout(resolve, delay))
            delay *= 2 // Backoff exponentiel
          } else {
            // Autre erreur ou plus de tentatives
            logger.error('Failed to fetch project', error, { projectId, retries })
            toast.error(error.response?.data?.detail || error.message || 'Impossible de charger le projet')
            setLoading(false)
            if (!isNotFound) {
              // Ne rediriger que si ce n'est pas une erreur 404 (projet pourrait exister)
              router.push('/projects')
            }
            return
          }
        }
      }
      
      // Si on arrive ici, toutes les tentatives ont échoué
      setLoading(false)
      toast.error('Impossible de charger le projet après plusieurs tentatives')
      router.push('/projects')
    }
    
    fetchData()
  }, [user, projectId, router])

  // Poll for active build updates
  useEffect(() => {
    if (!activeBuild || activeBuild.status === 'completed' || activeBuild.status === 'failed') return
    
    const interval = setInterval(async () => {
      if (!user?.id) return
      try {
        const updatedBuild = await buildsApi.getOne(activeBuild.id)
        setActiveBuild(updatedBuild)
        
        if (updatedBuild.status === 'completed') {
          toast.success('Build completed successfully!')
          setBuildingPlatform(null)
          // Refresh builds list
          const buildsData = await buildsApi.getAll(projectId)
          setBuilds(buildsData)
        } else if (updatedBuild.status === 'failed') {
          toast.error('Build failed')
          setBuildingPlatform(null)
        }
      } catch (error) {
        logger.error('Failed to fetch build status', error, { buildId: activeBuild.id, projectId })
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [activeBuild, user, projectId])

  const handleFeatureToggle = async (featureId: string, enabled: boolean) => {
    if (!project || !user?.id) return
    
    const updatedFeatures = project.features.map(f => 
      f.id === featureId ? { ...f, enabled } : f
    )
    
    try {
      await projectsApi.update(projectId, { features: updatedFeatures })
      setProject({ ...project, features: updatedFeatures })
      toast.success(`Feature ${enabled ? 'enabled' : 'disabled'}`)
    } catch (error) {
      toast.error('Failed to update feature')
    }
  }

  const ensureAndroidDependencies = async (): Promise<boolean> => {
    try {
      if (!session?.access_token) {
        toast.error('Authentification requise pour vérifier les dépendances')
        return false
      }
      
      const backendUrl = getBuildBackendUrl()
      const response = await fetch(`${backendUrl}/api/system/check-dependencies`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Erreur lors de la vérification des dépendances')
      }
      
      const data: DependenciesStatus = await response.json()
      if (!data.ready) {
        const firstError = data.errors?.[0]
        const message = firstError
          ? `Dépendances Android manquantes: ${firstError}`
          : 'Dépendances Android manquantes. Consultez la page Builds pour les instructions.'
        toast.error(message)
        return false
      }
      
      return true
    } catch (error) {
      logger.error('Failed to check Android dependencies before build', error)
      toast.error('Impossible de vérifier les dépendances Android')
      return false
    }
  }

  const handleStartBuild = async (platform: string) => {
    if (!user?.id || !project) return
    
    if (platform === 'android') {
      const canBuild = await ensureAndroidDependencies()
      if (!canBuild) return
    }
    
    setBuildingPlatform(platform)
    try {
      const build = await buildsApi.create({
        project_id: projectId,
        platform,
        build_type: 'debug'
      })
      
      setActiveBuild(build)
      setBuilds([build, ...builds])
      toast.success(`${platform} build started`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start build')
      setBuildingPlatform(null)
    }
  }

  const handleDeleteProject = async () => {
    if (!project || !user?.id) return
    
    setDeleting(true)
    try {
      await projectsApi.delete(projectId)
      toast.success('Projet supprimé avec succès')
      router.push('/projects')
    } catch (error: any) {
      logger.error('Erreur lors de la suppression du projet', error, { projectId })
      toast.error(error.response?.data?.detail || 'Échec de la suppression du projet')
      setDeleting(false)
    }
  }

  const handleDeleteBuildClick = (build: Build) => {
    setBuildToDelete(build)
    setDeleteBuildDialogOpen(true)
  }

  const handleDeleteBuildConfirm = async () => {
    if (!buildToDelete || !user?.id) return
    
    setDeleting(true)
    try {
      await buildsApi.delete(buildToDelete.id)
      setBuilds(builds.filter(b => b.id !== buildToDelete.id))
      toast.success('Build supprimé avec succès')
      setDeleteBuildDialogOpen(false)
      setBuildToDelete(null)
    } catch (error: any) {
      logger.error('Erreur lors de la suppression du build', error, { buildId: buildToDelete.id, projectId })
      toast.error(error.response?.data?.detail || 'Échec de la suppression du build')
    } finally {
      setDeleting(false)
    }
  }

  const handleGenerateScreenshots = async (store: 'ios' | 'android' | 'both' = 'both') => {
    if (!project || !user?.id) return
    
    setGeneratingScreenshots(true)
    try {
      // Utiliser apiClient pour gérer automatiquement l'authentification
      // Note: apiClient n'est pas exporté, on doit utiliser fetch avec l'URL correcte
      const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
      const API_URL = `${backendBaseUrl}/api`
      
      const { createClient } = await import('@/lib/supabase')
      const supabase = createClient()
      const { data: { session: currentSession } } = await supabase.auth.getSession()
      
      if (!currentSession?.access_token) {
        throw new Error('Not authenticated')
      }
      
      const response = await fetch(
        `${API_URL}/projects/${projectId}/screenshots/generate?store=${store}&auto_discover=true`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${currentSession.access_token}`,
          },
        }
      )
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to generate screenshots' }))
        throw new Error(error.detail || 'Failed to generate screenshots')
      }
      
      // Télécharger le ZIP
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `screenshots_${project.name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
      toast.success('Screenshots générés avec succès!')
    } catch (error: any) {
      logger.error('Screenshot generation error', error, { projectId, store })
      
      // Gérer les erreurs de manière plus détaillée
      let errorMessage = 'Erreur lors de la génération des screenshots'
      
      if (error.response) {
        // Erreur de réponse du serveur
        if (error.response.status === 401) {
          errorMessage = 'Authentification requise. Veuillez vous reconnecter.'
        } else if (error.response.status === 404) {
          errorMessage = 'Projet non trouvé ou accès non autorisé'
        } else if (error.response.status === 500) {
          errorMessage = error.response.data?.detail || 'Erreur serveur lors de la génération'
        } else {
          errorMessage = error.response.data?.detail || errorMessage
        }
      } else if (error.request) {
        // Pas de réponse du serveur
        errorMessage = 'Impossible de contacter le serveur. Vérifiez que le backend est démarré.'
      } else {
        // Erreur lors de la configuration de la requête
        errorMessage = error.message || errorMessage
      }
      
      toast.error(errorMessage)
    } finally {
      setGeneratingScreenshots(false)
    }
  }

  if (loading || !project) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <DashboardLayout 
      title={project.name} 
      subtitle={project.web_url}
      actions={
        <Button
          variant="outline"
          size="sm"
          className="border-destructive/30 text-destructive hover:bg-destructive/10 hover:border-destructive/50"
          onClick={() => setDeleteDialogOpen(true)}
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Supprimer
        </Button>
      }
    >
      {/* Dialog de confirmation de suppression du projet */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="bg-background-paper border-white/10">
          <DialogHeader>
            <DialogTitle className="text-destructive">Supprimer le projet</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir supprimer le projet <strong>"{project.name}"</strong> ? 
              <br />
              Cette action est <strong>irréversible</strong> et supprimera également tous les builds associés.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={deleting}
            >
              Annuler
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteProject}
              disabled={deleting}
            >
              {deleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Suppression...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Supprimer définitivement
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog de confirmation de suppression d'un build */}
      <Dialog open={deleteBuildDialogOpen} onOpenChange={setDeleteBuildDialogOpen}>
        <DialogContent className="bg-background-paper border-white/10">
          <DialogHeader>
            <DialogTitle className="text-destructive">Supprimer le build</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir supprimer ce build {buildToDelete ? `(${buildToDelete.platform.toUpperCase()})` : ''} ? 
              <br />
              Cette action est <strong>irréversible</strong>.
              {buildToDelete?.status === 'completed' && (
                <span className="block mt-2 text-warning">
                  ⚠️ Le fichier téléchargeable sera également supprimé.
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteBuildDialogOpen(false)
                setBuildToDelete(null)
              }}
              disabled={deleting}
            >
              Annuler
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteBuildConfirm}
              disabled={deleting}
            >
              {deleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Suppression...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Supprimer
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="bg-background-subtle">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="features">Features</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
          <TabsTrigger value="builds">Builds</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Project Info */}
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="w-5 h-5 text-primary" />
                  Project Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Web URL</p>
                  <a href={project.web_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    {project.web_url}
                  </a>
                </div>
                {project.description && (
                  <div>
                    <p className="text-sm text-muted-foreground">Description</p>
                    <p>{project.description}</p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-muted-foreground">Platforms</p>
                  <div className="flex gap-2 mt-1">
                    {project.platform.includes('android') && (
                      <Badge variant="outline" className="text-success border-success/30">
                        <Smartphone className="w-3 h-3 mr-1" /> Android
                      </Badge>
                    )}
                    {project.platform.includes('ios') && (
                      <Badge variant="outline" className="text-info border-info/30">
                        <Apple className="w-3 h-3 mr-1" /> iOS
                      </Badge>
                    )}
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <Badge variant={project.status === 'active' ? 'success' : 'warning'}>
                    {project.status}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Build Actions */}
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Play className="w-5 h-5 text-primary" />
                  Build Actions
                </CardTitle>
                <CardDescription>
                  Start a new build for your project
                  <span className="block text-xs text-muted-foreground">
                    Build backend: {buildBackendConfig.mode === 'local' ? 'Local' : 'Remote'} ({buildBackendConfig.url})
                  </span>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {project.platform.includes('android') && (
                  <Button
                    className="w-full justify-start bg-success/10 text-success hover:bg-success/20 border border-success/30"
                    onClick={() => handleStartBuild('android')}
                    disabled={buildingPlatform !== null}
                    data-testid="build-android-btn"
                  >
                    {buildingPlatform === 'android' ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Smartphone className="w-4 h-4 mr-2" />
                    )}
                    Build for Android
                  </Button>
                )}
                {project.platform.includes('ios') && (
                  <Button
                    className="w-full justify-start bg-info/10 text-info hover:bg-info/20 border border-info/30"
                    onClick={() => handleStartBuild('ios')}
                    disabled={buildingPlatform !== null}
                    data-testid="build-ios-btn"
                  >
                    {buildingPlatform === 'ios' ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Apple className="w-4 h-4 mr-2" />
                    )}
                    Build for iOS
                  </Button>
                )}

                {/* Active Build Progress */}
                {activeBuild && activeBuild.status === 'processing' && (
                  <div className="mt-6 p-4 rounded-lg border border-primary/30 bg-primary/5">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Building {activeBuild.platform}...</span>
                      <span className="text-sm text-primary">{activeBuild.progress}%</span>
                    </div>
                    <Progress value={activeBuild.progress} className="h-2" />
                    <p className="text-xs text-muted-foreground mt-2">{activeBuild.phase}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Features Tab */}
        <TabsContent value="features">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-primary" />
                Native Features
              </CardTitle>
              <CardDescription>Configure which native features your app will use</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {project.features.map((feature) => (
                  <div
                    key={feature.id}
                    className="flex items-center justify-between p-4 rounded-lg border border-white/10 hover:border-white/20 transition-colors"
                    data-testid={`feature-${feature.id}`}
                  >
                    <div>
                      <p className="font-medium">{feature.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {feature.enabled ? 'Enabled' : 'Disabled'}
                      </p>
                    </div>
                    <Switch
                      checked={feature.enabled}
                      onCheckedChange={(checked) => handleFeatureToggle(feature.id, checked)}
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Configuration Tab */}
        <TabsContent value="advanced">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Screen Orientation */}
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Monitor className="w-5 h-5 text-primary" />
                  Screen Orientation
                </CardTitle>
                <CardDescription>Control how your app handles device rotation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Orientation Mode</label>
                  <select
                    value={orientation}
                    onChange={(e) => setOrientation(e.target.value as 'portrait' | 'landscape' | 'sensor')}
                    className="w-full px-3 py-2 bg-background border border-white/10 rounded-md text-foreground"
                  >
                    <option value="sensor">Auto (Sensor-based)</option>
                    <option value="portrait">Portrait Only</option>
                    <option value="landscape">Landscape Only</option>
                  </select>
                  <p className="text-xs text-muted-foreground">
                    Choose how your app responds to device rotation
                  </p>
                </div>
                <Button
                  onClick={async () => {
                    try {
                      const currentAdvancedConfig = (project as any).advanced_config || {}
                      await projectsApi.update(projectId, {
                        advanced_config: {
                          ...currentAdvancedConfig,
                          orientation: orientation
                        }
                      })
                      toast.success('Orientation configuration saved')
                    } catch (error: any) {
                      logger.error('Failed to save orientation', error)
                      toast.error(error.response?.data?.detail || 'Failed to save orientation')
                    }
                  }}
                  className="w-full"
                >
                  Save Orientation
                </Button>
              </CardContent>
            </Card>

            {/* Status Bar */}
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Palette className="w-5 h-5 text-primary" />
                  Status Bar
                </CardTitle>
                <CardDescription>Customize the status bar appearance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Status Bar Style</label>
                  <select
                    value={statusBarStyle}
                    onChange={(e) => setStatusBarStyle(e.target.value as 'light' | 'dark')}
                    className="w-full px-3 py-2 bg-background border border-white/10 rounded-md text-foreground"
                  >
                    <option value="dark">Dark (Light icons)</option>
                    <option value="light">Light (Dark icons)</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Status Bar Color</label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={statusBarColor}
                      onChange={(e) => setStatusBarColor(e.target.value)}
                      className="w-16 h-10 rounded border border-white/10"
                    />
                    <input
                      type="text"
                      value={statusBarColor}
                      onChange={(e) => setStatusBarColor(e.target.value)}
                      className="flex-1 px-3 py-2 bg-background border border-white/10 rounded-md text-foreground"
                      placeholder="#000000"
                    />
                  </div>
                </div>
                <Button
                  onClick={async () => {
                    try {
                      const currentAdvancedConfig = (project as any).advanced_config || {}
                      await projectsApi.update(projectId, {
                        advanced_config: {
                          ...currentAdvancedConfig,
                          status_bar: {
                            style: statusBarStyle,
                            color: statusBarColor
                          }
                        }
                      })
                      toast.success('Status bar configuration saved')
                    } catch (error: any) {
                      logger.error('Failed to save status bar', error)
                      toast.error(error.response?.data?.detail || 'Failed to save status bar')
                    }
                  }}
                  className="w-full"
                >
                  Save Status Bar
                </Button>
              </CardContent>
            </Card>

            {/* Splash Screen */}
            <Card className="bg-background-paper border-white/10 lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ImageIcon className="w-5 h-5 text-primary" />
                  Splash Screen
                </CardTitle>
                <CardDescription>Configure your app's splash screen</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Splash Screen Image</label>
                  <div className="border-2 border-dashed border-white/10 rounded-lg p-6 text-center">
                    <ImageIcon className="w-12 h-12 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground mb-2">
                      Upload a splash screen image (recommended: 1080x1920px)
                    </p>
                    <Button variant="outline" size="sm">
                      Upload Image
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    The splash screen will be displayed when your app launches
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Store Screenshots Generator */}
            <Card className="bg-background-paper border-white/10 lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Rocket className="w-5 h-5 text-primary" />
                  Store Screenshots Generator
                </CardTitle>
                <CardDescription>
                  Génère automatiquement tous les screenshots requis pour App Store et Play Store
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Ce générateur va automatiquement :
                  </p>
                  <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
                    <li>Découvrir les pages importantes de votre application</li>
                    <li>Capturer des screenshots dans toutes les résolutions requises</li>
                    <li>Générer un ZIP prêt à être uploadé sur les stores</li>
                  </ul>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Button
                    onClick={() => handleGenerateScreenshots('ios')}
                    disabled={generatingScreenshots}
                    className="w-full"
                    variant="outline"
                  >
                    {generatingScreenshots ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Apple className="w-4 h-4 mr-2" />
                    )}
                    iOS Only
                  </Button>
                  
                  <Button
                    onClick={() => handleGenerateScreenshots('android')}
                    disabled={generatingScreenshots}
                    className="w-full"
                    variant="outline"
                  >
                    {generatingScreenshots ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Smartphone className="w-4 h-4 mr-2" />
                    )}
                    Android Only
                  </Button>
                  
                  <Button
                    onClick={() => handleGenerateScreenshots('both')}
                    disabled={generatingScreenshots}
                    className="w-full bg-primary"
                  >
                    {generatingScreenshots ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Rocket className="w-4 h-4 mr-2" />
                    )}
                    Both Stores
                  </Button>
                </div>
                
                {generatingScreenshots && (
                  <div className="p-4 rounded-lg border border-primary/30 bg-primary/5">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-primary" />
                      <p className="text-sm text-muted-foreground">
                        Génération en cours... Cela peut prendre quelques minutes.
                      </p>
                    </div>
                  </div>
                )}

                <div className="p-4 rounded-lg border border-info/20 bg-info/5">
                  <p className="text-xs text-muted-foreground">
                    <strong>Note:</strong> Les screenshots seront générés dans les résolutions exactes requises :
                  </p>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                    <div>
                      <strong>iOS:</strong> iPhone 6.7", 6.5", 5.5", iPad Pro 12.9", 11", 10.5"
                    </div>
                    <div>
                      <strong>Android:</strong> Phone, 7" Tablet, 10" Tablet, TV, Wear
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Builds Tab */}
        <TabsContent value="builds">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>Build History</CardTitle>
              <CardDescription>All builds for this project</CardDescription>
            </CardHeader>
            <CardContent>
              {builds.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No builds yet</p>
                  <p className="text-sm text-muted-foreground">Start a build from the Overview tab</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <div className="space-y-3">
                    {builds.map((build) => (
                      <div
                        key={build.id}
                        className="flex items-center justify-between p-4 rounded-lg border border-white/10"
                        data-testid={`build-item-${build.id}`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            build.platform === 'android' ? 'bg-success/10' : 'bg-info/10'
                          }`}>
                            {build.platform === 'android' ? (
                              <Smartphone className="w-5 h-5 text-success" />
                            ) : (
                              <Apple className="w-5 h-5 text-info" />
                            )}
                          </div>
                          <div>
                            <p className="font-medium">
                              {build.platform.charAt(0).toUpperCase() + build.platform.slice(1)} Build
                            </p>
                            <p className="text-xs text-muted-foreground flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(build.created_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          {build.status === 'completed' && (
                            <Badge variant="success" className="flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" />
                              Completed
                            </Badge>
                          )}
                          {build.status === 'processing' && (
                            <Badge className="flex items-center gap-1 bg-primary/20 text-primary">
                              <Loader2 className="w-3 h-3 animate-spin" />
                              {build.progress}%
                            </Badge>
                          )}
                          {build.status === 'failed' && (
                            <Badge variant="destructive" className="flex items-center gap-1">
                              <XCircle className="w-3 h-3" />
                              Failed
                            </Badge>
                          )}
                          {build.status === 'pending' && (
                            <Badge variant="warning" className="flex items-center gap-1">
                              <AlertCircle className="w-3 h-3" />
                              Pending
                            </Badge>
                          )}
                          {build.status === 'completed' && (
                            <div className="flex items-center gap-2">
                              <Badge variant="success" className="flex items-center gap-1 text-xs">
                                <CheckCircle2 className="w-3 h-3" />
                                Prêt
                              </Badge>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className={`border-white/10 ${
                                  build.platform === 'android' 
                                    ? 'hover:bg-success/10 hover:border-success/30' 
                                    : 'hover:bg-info/10 hover:border-info/30'
                                }`}
                                onClick={() => download(build.id, build.platform)}
                                disabled={isDownloading}
                              >
                                {isDownloading ? (
                                  <>
                                    <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                                    {progress.toFixed(0)}%
                                  </>
                                ) : (
                                  <>
                                    <Download className="w-4 h-4 mr-1" />
                                    {build.platform === 'android' ? 'APK' : 'IPA'}
                                  </>
                                )}
                              </Button>
                              {build.platform === 'android' ? (
                                <Button 
                                  size="sm" 
                                  className="bg-success hover:bg-success/90 text-xs"
                                  onClick={() => {
                                    // Redirection directe vers Google Play Console
                                    window.open('https://play.google.com/console', '_blank')
                                  }}
                                >
                                  <Rocket className="w-3 h-3 mr-1" />
                                  Publier sur Play Store
                                </Button>
                              ) : (
                                <Button 
                                  size="sm" 
                                  className="bg-info hover:bg-info/90 text-xs"
                                  onClick={() => {
                                    // Redirection directe vers App Store Connect
                                    window.open('https://appstoreconnect.apple.com', '_blank')
                                  }}
                                >
                                  <Rocket className="w-3 h-3 mr-1" />
                                  Publier sur App Store
                                </Button>
                              )}
                            </div>
                          )}
                          {/* Bouton de suppression */}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-muted-foreground hover:text-destructive"
                            onClick={() => handleDeleteBuildClick(build)}
                            disabled={build.status === 'processing'}
                            data-testid={`delete-build-${build.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  )
}
