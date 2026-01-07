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
import { toast } from 'sonner'
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
  AlertCircle
} from 'lucide-react'

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

export default function ProjectDetailPage() {
  const { user } = useAuth()
  const router = useRouter()
  const params = useParams()
  const projectId = params.id as string
  
  const [project, setProject] = useState<Project | null>(null)
  const [builds, setBuilds] = useState<Build[]>([])
  const [availableFeatures, setAvailableFeatures] = useState<Feature[]>([])
  const [loading, setLoading] = useState(true)
  const [buildingPlatform, setBuildingPlatform] = useState<string | null>(null)
  const [activeBuild, setActiveBuild] = useState<Build | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      if (!user?.id || !projectId) return
      
      setLoading(true)
      let retries = 3
      let delay = 500
      
      while (retries > 0) {
        try {
          const [projectData, buildsData, featuresData] = await Promise.all([
            projectsApi.getOne(projectId),
            buildsApi.getAll(projectId).catch(() => []), // Ne pas bloquer si les builds échouent
            featuresApi.getAll().catch(() => []) // Ne pas bloquer si les features échouent
          ])
          
          setProject(projectData)
          setBuilds(buildsData || [])
          setAvailableFeatures(featuresData || [])
          setLoading(false)
          return // Succès, sortir de la boucle
        } catch (error: any) {
          retries--
          const isNotFound = error.response?.status === 404
          const isConnectionError = error.isConnectionError || error.code === 'ECONNREFUSED'
          
          if (isConnectionError) {
            // Erreur de connexion, ne pas réessayer
            console.error('Backend connection error:', error)
            toast.error('Impossible de se connecter au serveur. Vérifiez que le backend est démarré.')
            setLoading(false)
            router.push('/projects')
            return
          }
          
          if (isNotFound && retries > 0) {
            // Projet pas encore disponible, réessayer après un délai
            console.warn(`Project not found (retries left: ${retries}), retrying in ${delay}ms...`)
            await new Promise(resolve => setTimeout(resolve, delay))
            delay *= 2 // Backoff exponentiel
          } else {
            // Autre erreur ou plus de tentatives
            console.error('Failed to fetch project:', error)
            toast.error(error.response?.data?.detail || 'Impossible de charger le projet')
            setLoading(false)
            router.push('/projects')
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
        console.error('Failed to fetch build status:', error)
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

  const handleStartBuild = async (platform: string) => {
    if (!user?.id || !project) return
    
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

  if (loading || !project) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <DashboardLayout title={project.name} subtitle={project.web_url}>
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="bg-background-subtle">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="features">Features</TabsTrigger>
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
                <CardDescription>Start a new build for your project</CardDescription>
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
                                onClick={async () => {
                                  try {
                                    const blob = await buildsApi.download(build.id)
                                    const url = window.URL.createObjectURL(blob)
                                    const a = document.createElement('a')
                                    a.href = url
                                    a.download = `app-${build.platform}-${Date.now()}.${build.platform === 'android' ? 'apk' : 'ipa'}`
                                    document.body.appendChild(a)
                                    a.click()
                                    window.URL.revokeObjectURL(url)
                                    document.body.removeChild(a)
                                    toast.success('Téléchargement démarré !')
                                  } catch (error: any) {
                                    console.error('Erreur de téléchargement:', error)
                                    toast.error(error.response?.data?.detail || 'Erreur lors du téléchargement')
                                  }
                                }}
                              >
                                <Download className="w-4 h-4 mr-1" />
                                {build.platform === 'android' ? 'APK' : 'IPA'}
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
