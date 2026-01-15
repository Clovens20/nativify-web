'use client'

import { useTrackVisit } from '@/hooks/useTrackVisit'

export function VisitTracker() {
  useTrackVisit()
  return null // Ce composant ne rend rien, il track juste les visites
}

