'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CheckCircle2, XCircle, AlertCircle, Loader2, RefreshCw, Settings } from 'lucide-react'
import { toast } from 'sonner'
import { logger } from '@/lib/logger'

interface DependenciesStatus {
  android_builder_available: boolean
  java_available: boolean
  java_version: string | null
  java_home: string | null
  android_sdk_available: boolean
  android_home: string | null
  gradle_available: boolean
  status: string
  ready: boolean
  errors: string[]
  warnings: string[]
  instructions: string[]
}

export function DependenciesChecker() {
  const [status, setStatus] = useState<DependenciesStatus | null>(null)
  const [loading, setLoading] = useState(true)

  const checkDependencies = async () => {
    setLoading(true)
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
      const { createClient } = await import('@/lib/supabase')
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        throw new Error('Vous devez être connecté')
      }

      const response = await fetch(`${backendUrl}/api/system/check-dependencies`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      })

      if (!response.ok) {
        throw new Error('Erreur lors de la vérification')
      }

      const data = await response.json()
      setStatus(data)
    } catch (error: any) {
      logger.error('Failed to check dependencies', error)
      toast.error('Erreur lors de la vérification des dépendances')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkDependencies()
  }, [])

  if (loading) {
    return (
      <Card className="bg-background-paper border-white/10">
        <CardContent className="p-6">
          <div className="flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Vérification des dépendances...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!status) {
    return null
  }

  return (
    <Card className="bg-background-paper border-white/10">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5 text-primary" />
              État du Système
            </CardTitle>
            <CardDescription>Vérification des dépendances pour la compilation Android</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={checkDependencies}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Actualiser
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Statut global */}
        <div className="flex items-center gap-2">
          {status.ready ? (
            <>
              <CheckCircle2 className="w-5 h-5 text-success" />
              <span className="font-medium text-success">Système prêt pour la compilation</span>
            </>
          ) : (
            <>
              <XCircle className="w-5 h-5 text-destructive" />
              <span className="font-medium text-destructive">Dépendances manquantes</span>
            </>
          )}
        </div>

        {/* Détails */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm">Android Builder</span>
            <Badge variant={status.android_builder_available ? "success" : "destructive"}>
              {status.android_builder_available ? "Disponible" : "Non disponible"}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm">Java JDK</span>
            <div className="flex items-center gap-2">
              {status.java_available ? (
                <>
                  <Badge variant="success">Installé</Badge>
                  {status.java_version && (
                    <span className="text-xs text-muted-foreground">{status.java_version}</span>
                  )}
                </>
              ) : (
                <Badge variant="destructive">Non installé</Badge>
              )}
            </div>
          </div>

          {status.java_home && (
            <div className="text-xs text-muted-foreground pl-4">
              JAVA_HOME: {status.java_home}
            </div>
          )}

          <div className="flex items-center justify-between">
            <span className="text-sm">Android SDK</span>
            <Badge variant={status.android_sdk_available ? "success" : "warning"}>
              {status.android_sdk_available ? "Installé" : "Optionnel"}
            </Badge>
          </div>

          {status.android_home && (
            <div className="text-xs text-muted-foreground pl-4">
              ANDROID_HOME: {status.android_home}
            </div>
          )}

          <div className="flex items-center justify-between">
            <span className="text-sm">Gradle</span>
            <Badge variant="success">Auto-téléchargé</Badge>
          </div>
        </div>

        {/* Erreurs */}
        {status.errors.length > 0 && (
          <div className="p-3 rounded-lg border border-destructive/30 bg-destructive/5">
            <div className="flex items-center gap-2 mb-2">
              <XCircle className="w-4 h-4 text-destructive" />
              <span className="text-sm font-medium text-destructive">Erreurs</span>
            </div>
            <ul className="text-xs text-muted-foreground list-disc list-inside space-y-1">
              {status.errors.map((error, idx) => (
                <li key={idx}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Avertissements */}
        {status.warnings.length > 0 && (
          <div className="p-3 rounded-lg border border-warning/30 bg-warning/5">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-4 h-4 text-warning" />
              <span className="text-sm font-medium text-warning">Avertissements</span>
            </div>
            <ul className="text-xs text-muted-foreground list-disc list-inside space-y-1">
              {status.warnings.map((warning, idx) => (
                <li key={idx}>{warning}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Instructions */}
        {status.instructions.length > 0 && (
          <div className="p-3 rounded-lg border border-info/30 bg-info/5">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-4 h-4 text-info" />
              <span className="text-sm font-medium text-info">Instructions</span>
            </div>
            <ol className="text-xs text-muted-foreground list-decimal list-inside space-y-1">
              {status.instructions.map((instruction, idx) => (
                <li key={idx}>{instruction}</li>
              ))}
            </ol>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

