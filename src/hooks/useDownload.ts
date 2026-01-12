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

  const download = async (buildId: string) => {
    try {
      setIsDownloading(true)
      setProgress(0)
      setDownloadedSize(0)
      setTotalSize(0)
      
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
      })
      
      toast.success('Téléchargement réussi', {
        description: 'L\'APK a été téléchargé avec succès',
      })
      
      return { success: true }
    } catch (error) {
      console.error('Download failed:', error)
      
      toast.error('Erreur de téléchargement', {
        description: error instanceof Error ? error.message : 'Échec du téléchargement',
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

