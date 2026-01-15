'use client'

import { useState } from 'react'
import { buildsApi } from '@/lib/api'
import { toast } from 'sonner'
import { createClient } from '@/lib/supabase'

export function useDownload() {
  const [isDownloading, setIsDownloading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [downloadedSize, setDownloadedSize] = useState(0)
  const [totalSize, setTotalSize] = useState(0)

  const download = async (buildId: string, platform: string = 'android') => {
    try {
      setIsDownloading(true)
      setProgress(0)
      setDownloadedSize(0)
      setTotalSize(0)
      
      // Afficher un toast informatif pour Android (compilation peut prendre du temps)
      if (platform === 'android') {
        toast.info('Compilation de l\'APK en cours...', {
          description: 'Cela peut prendre quelques minutes. Veuillez patienter.',
          duration: 10000
        })
      }
      
      // Récupérer le token depuis la session Supabase
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      
      if (!session?.access_token) {
        throw new Error('Vous devez être connecté pour télécharger')
      }
      
      await buildsApi.downloadWithProgress(
        buildId,
        (prog, loaded, total) => {
          setProgress(prog)
          setDownloadedSize(loaded)
          setTotalSize(total)
        }
      ).then(async ({ blob, filename }) => {
        // Vérifier le type de fichier téléchargé
        const isAPK = filename.endsWith('.apk') || blob.type === 'application/vnd.android.package-archive'
        const isZIP = filename.endsWith('.zip') || blob.type === 'application/zip'
        
        // Créer un lien de téléchargement temporaire
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = url
        a.download = filename
        
        // Ajouter au DOM, cliquer, puis nettoyer
        document.body.appendChild(a)
        a.click()
        
        // Attendre un peu avant de nettoyer (pour les navigateurs lents)
        setTimeout(() => {
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)
        }, 100)
        
        // Afficher un message approprié selon le type de fichier
        if (isAPK && platform === 'android') {
          toast.success('APK compilé et téléchargé avec succès!', {
            description: 'Vous pouvez maintenant installer l\'APK sur votre appareil Android.',
            duration: 5000
          })
        } else if (isZIP && platform === 'android') {
          toast.warning('Projet source téléchargé', {
            description: 'La compilation a échoué. Un projet source (ZIP) a été fourni. Vérifiez les dépendances système.',
            duration: 8000
          })
        } else {
          toast.success('Téléchargement réussi', {
            description: `Le fichier ${filename} a été téléchargé avec succès`,
            duration: 5000
          })
        }
      })
      
      return { success: true }
    } catch (error: any) {
      console.error('Download failed:', error)
      
      // Essayer d'extraire des informations d'erreur détaillées
      let errorMessage = 'Échec du téléchargement'
      let errorDescription = error instanceof Error ? error.message : 'Une erreur est survenue'
      
      // Si c'est une erreur de réponse HTTP, essayer d'extraire plus d'infos
      if (error.response?.data) {
        try {
          // Si c'est un blob avec du JSON dedans
          if (error.response.data instanceof Blob) {
            const text = await error.response.data.text()
            try {
              const errorData = JSON.parse(text)
              if (errorData.detail) {
                if (typeof errorData.detail === 'string') {
                  errorMessage = errorData.detail
                } else if (errorData.detail.message) {
                  errorMessage = errorData.detail.message
                  errorDescription = errorData.detail.instructions?.join(' ') || errorDescription
                }
              }
            } catch {
              // Ce n'est pas du JSON, utiliser le texte brut
              errorMessage = text.substring(0, 200)
            }
          } else if (typeof error.response.data === 'object') {
            errorMessage = error.response.data.detail || errorMessage
          }
        } catch {
          // Ignorer les erreurs de parsing
        }
      }
      
      toast.error(errorMessage, {
        description: errorDescription,
        duration: 10000
      })
      
      return { success: false, error }
    } finally {
      setIsDownloading(false)
      setProgress(0)
      setDownloadedSize(0)
      setTotalSize(0)
    }
  }

  return {
    download,
    isDownloading,
    progress,
    downloadedSize,
    totalSize,
  }
}

