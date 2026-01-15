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
import { toast } from 'sonner'
import { logger } from '@/lib/logger'
import { useDownload } from '@/hooks/useDownload'
import { DependenciesChecker } from '@/components/system/DependenciesChecker'
import { 
  Smartphone, 
  Apple, 
  Download,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Rocket,
  Info,
  Trash2,
  Trash
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
// Modals conservés pour référence future si nécessaire
// import { PlayStoreModal } from '@/components/publication/PlayStoreModal'
// import { AppStoreModal } from '@/components/publication/AppStoreModal'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

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
  const { download, isDownloading, progress } = useDownload()
  const [builds, setBuilds] = useState<Build[]>([])
  const [projects, setProjects] = useState<Record<string, Project>>({})
  const [loading, setLoading] = useState(true)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteAllDialogOpen, setDeleteAllDialogOpen] = useState(false)
  const [buildToDelete, setBuildToDelete] = useState<Build | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  const fetchData = async () => {
    if (!user?.id) return
    try {
      const [buildsData, projectsData] = await Promise.all([
        buildsApi.getAll(),
        projectsApi.getAll(true) // Utiliser le cache pour les projets
      ])
      setBuilds(buildsData)
      
      // Create a map of projects
      const projectsMap: Record<string, Project> = {}
      if (projectsData && Array.isArray(projectsData)) {
        projectsData.forEach((p: Project) => {
          if (p && p.id && p.name) {
            projectsMap[p.id] = p
          }
        })
      }
      
      // Charger les projets manquants pour les builds qui n'ont pas de projet dans la map
      if (buildsData && buildsData.length > 0) {
        const missingProjectIds = new Set<string>()
        buildsData.forEach((b: Build) => {
          if (b.project_id && !projectsMap[b.project_id]) {
            missingProjectIds.add(b.project_id)
          }
        })
        
        // Charger chaque projet manquant
        if (missingProjectIds.size > 0) {
          const missingProjectsPromises = Array.from(missingProjectIds).map(async (projectId: string) => {
            try {
              const project = await projectsApi.getOne(projectId, true)
              if (project && project.id && project.name) {
                projectsMap[project.id] = project
              }
            } catch (error) {
              // Projet peut-être supprimé ou inaccessible, on l'ignore
              logger.debug('Project not found', { projectId })
            }
          })
          
          await Promise.all(missingProjectsPromises)
        }
      }
      
      setProjects(projectsMap)
      
      // Log pour débugger si nécessaire
      if (buildsData && buildsData.length > 0) {
        const stillMissing = buildsData.filter((b: Build) => !projectsMap[b.project_id])
        if (stillMissing.length > 0) {
          const uniqueMissingIds = Array.from(new Set(stillMissing.map((b: Build) => b.project_id)))
          logger.warn('Some builds have missing projects (after loading)', {
            missingCount: stillMissing.length,
            missingProjectIds: uniqueMissingIds,
            totalProjects: Object.keys(projectsMap).length,
            totalBuilds: buildsData.length
          })
        }
      }
    } catch (error: any) {
      logger.error('Failed to fetch builds', error, { userId: user?.id })
      if (error.isConnectionError) {
        toast.error('Impossible de se connecter au serveur. Vérifiez que le backend est démarré.')
      } else {
        toast.error(error.response?.data?.detail || 'Échec du chargement des builds')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [user])

  const handleDeleteClick = (build: Build) => {
    setBuildToDelete(build)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!buildToDelete || !user?.id) return
    
    setDeleting(true)
    try {
      await buildsApi.delete(buildToDelete.id)
      setBuilds(builds.filter(b => b.id !== buildToDelete.id))
      toast.success('Build supprimé avec succès')
      setDeleteDialogOpen(false)
      setBuildToDelete(null)
    } catch (error: any) {
      logger.error('Erreur lors de la suppression du build', error, { buildId: buildToDelete.id })
      toast.error(error.response?.data?.detail || 'Échec de la suppression du build')
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteAllClick = () => {
    if (builds.length === 0) return
    setDeleteAllDialogOpen(true)
  }

  const handleDeleteAllConfirm = async () => {
    if (!user?.id || builds.length === 0) return
    
    setDeleting(true)
    try {
      await buildsApi.deleteAll()
      setBuilds([])
      toast.success(`Tous les builds ont été supprimés (${builds.length} builds)`)
      setDeleteAllDialogOpen(false)
    } catch (error: any) {
      logger.error('Erreur lors de la suppression de tous les builds', error, { count: builds.length, userId: user?.id })
      toast.error(error.response?.data?.detail || 'Échec de la suppression des builds')
    } finally {
      setDeleting(false)
    }
  }

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
      {/* Vérification des dépendances système */}
      <div className="mb-6">
        <DependenciesChecker />
      </div>

      {/* Dialog de confirmation de suppression d'un build */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="bg-background-paper border-white/10">
          <DialogHeader>
            <DialogTitle className="text-destructive">Supprimer le build</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir supprimer ce build pour <strong>"{buildToDelete ? projects[buildToDelete.project_id]?.name || `Build ${buildToDelete.id.substring(0, 8)}` : ''}"</strong> ? 
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
                setDeleteDialogOpen(false)
                setBuildToDelete(null)
              }}
              disabled={deleting}
            >
              Annuler
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
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

      {/* Dialog de confirmation de suppression de tout l'historique */}
      <Dialog open={deleteAllDialogOpen} onOpenChange={setDeleteAllDialogOpen}>
        <DialogContent className="bg-background-paper border-white/10">
          <DialogHeader>
            <DialogTitle className="text-destructive">Supprimer tout l'historique</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir supprimer <strong>tous les builds</strong> ({builds.length} build{builds.length > 1 ? 's' : ''}) ?
              <br />
              Cette action est <strong>irréversible</strong> et supprimera tous les fichiers téléchargeables.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteAllDialogOpen(false)}
              disabled={deleting}
            >
              Annuler
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteAllConfirm}
              disabled={deleting}
            >
              {deleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Suppression...
                </>
              ) : (
                <>
                  <Trash className="w-4 h-4 mr-2" />
                  Supprimer tout ({builds.length})
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card className="bg-background-paper border-white/10">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Build History</CardTitle>
              <CardDescription>All builds across your projects</CardDescription>
            </div>
            {builds.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                className="border-destructive/30 text-destructive hover:bg-destructive/10 hover:border-destructive/50"
                onClick={handleDeleteAllClick}
              >
                <Trash className="w-4 h-4 mr-2" />
                Supprimer tout
              </Button>
            )}
          </div>
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
                        {projects[build.project_id]?.name || `Build ${build.id.substring(0, 8)}`}
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
                    
                    {/* Bouton de suppression pour chaque build */}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-destructive"
                      onClick={() => handleDeleteClick(build)}
                      disabled={build.status === 'processing'}
                      data-testid={`delete-build-${build.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                    
                    {build.status === 'completed' && (
                      <div className="flex items-center gap-2">
                        {/* Badge Prêt à publier */}
                        <Badge variant="success" className="flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          Prêt à publier
                        </Badge>

                        {/* Bouton de téléchargement spécifique à la plateforme */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
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
                                    Téléchargement... {progress.toFixed(0)}%
                                  </>
                                ) : (
                                  <>
                                    <Download className="w-4 h-4 mr-1" />
                                    {build.platform === 'android' ? 'Télécharger APK' : 'Télécharger IPA'}
                                  </>
                                )}
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Télécharger le fichier {build.platform === 'android' ? 'APK' : 'IPA'} sur votre appareil</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>

                        {/* Bouton de publication vers les stores - Redirection directe */}
                        {build.platform === 'android' ? (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button 
                                  size="sm" 
                                  className="bg-success hover:bg-success/90"
                                  onClick={() => {
                                    // Redirection directe vers Google Play Console
                                    window.open('https://play.google.com/console', '_blank')
                                  }}
                                >
                                  <Rocket className="w-4 h-4 mr-1" />
                                  Publier sur Play Store
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Ouvrir Google Play Console pour publier votre application</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        ) : (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button 
                                  size="sm" 
                                  className="bg-info hover:bg-info/90"
                                  onClick={() => {
                                    // Redirection directe vers App Store Connect
                                    window.open('https://appstoreconnect.apple.com', '_blank')
                                  }}
                                >
                                  <Rocket className="w-4 h-4 mr-1" />
                                  Publier sur App Store
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Ouvrir App Store Connect pour publier votre application</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}

                        {/* Info tooltip */}
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button 
                                size="sm" 
                                variant="ghost" 
                                className="text-muted-foreground hover:text-foreground"
                              >
                                <Info className="w-4 h-4" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-xs">
                              <p className="text-xs">
                                Votre application est prête ! Téléchargez le fichier {build.platform === 'android' ? 'APK' : 'IPA'} 
                                et suivez notre guide pour publier sur les stores officiels.
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </div>
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
