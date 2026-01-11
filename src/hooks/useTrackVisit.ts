'use client'

import { useEffect } from 'react'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { logger } from '@/lib/logger'

// Fonction pour détecter le type d'appareil
function getDeviceType(): string {
  if (typeof window === 'undefined') return 'unknown'
  
  const width = window.innerWidth
  if (width < 768) return 'mobile'
  if (width < 1024) return 'tablet'
  return 'desktop'
}

// Fonction pour obtenir le navigateur
function getBrowser(): string {
  if (typeof window === 'undefined') return 'unknown'
  
  const ua = window.navigator.userAgent
  if (ua.indexOf('Chrome') > -1) return 'Chrome'
  if (ua.indexOf('Firefox') > -1) return 'Firefox'
  if (ua.indexOf('Safari') > -1) return 'Safari'
  if (ua.indexOf('Edge') > -1) return 'Edge'
  return 'unknown'
}

// Fonction pour obtenir l'OS
function getOS(): string {
  if (typeof window === 'undefined') return 'unknown'
  
  const ua = window.navigator.userAgent
  if (ua.indexOf('Windows') > -1) return 'Windows'
  if (ua.indexOf('Mac') > -1) return 'macOS'
  if (ua.indexOf('Linux') > -1) return 'Linux'
  if (ua.indexOf('Android') > -1) return 'Android'
  if (ua.indexOf('iOS') > -1 || ua.indexOf('iPhone') > -1 || ua.indexOf('iPad') > -1) return 'iOS'
  return 'unknown'
}

// Fonction pour obtenir ou créer un session_id
function getSessionId(): string {
  if (typeof window === 'undefined') return ''
  
  let sessionId = sessionStorage.getItem('visit_session_id')
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    sessionStorage.setItem('visit_session_id', sessionId)
  }
  return sessionId
}

export function useTrackVisit() {
  const pathname = usePathname()
  const { user } = useAuth()

  useEffect(() => {
    // Ne pas tracker les visites sur les pages admin pour éviter le bruit
    if (pathname?.startsWith('/admin')) return
    
    // Attendre un peu pour s'assurer que la page est chargée
    const timer = setTimeout(() => {
      trackVisit()
    }, 1000)

    return () => clearTimeout(timer)
  }, [pathname, user])

  const trackVisit = async () => {
    try {
      const sessionId = getSessionId()
      
      const visitData = {
        page_path: pathname || '/',
        user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
        referrer: typeof document !== 'undefined' ? document.referrer : undefined,
        device_type: getDeviceType(),
        browser: getBrowser(),
        os: getOS(),
        session_id: sessionId,
        user_id: user?.id || null
      }

      // Envoyer au backend de manière asynchrone (ne pas bloquer)
      // In development, use relative URL (proxied by Next.js)
      // In production, use absolute URL from env variable
      const API_URL = process.env.NODE_ENV === 'production'
        ? (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000') + '/api'
        : '/api'
      fetch(`${API_URL}/track-visit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(visitData),
      }).catch((error) => {
        // Ignorer les erreurs silencieusement pour ne pas perturber l'expérience utilisateur
        logger.debug('Visit tracking error', { error })
      })
    } catch (error) {
      // Ignorer les erreurs silencieusement
      logger.debug('Visit tracking error', { error })
    }
  }
}

