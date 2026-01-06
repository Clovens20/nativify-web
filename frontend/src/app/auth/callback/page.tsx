'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'

export default function AuthCallbackPage() {
  const router = useRouter()

  useEffect(() => {
    const handleCallback = async () => {
      const supabase = createClient()
      
      // Handle the OAuth callback
      const { error } = await supabase.auth.exchangeCodeForSession(window.location.href)
      
      if (error) {
        console.error('Auth callback error:', error)
        router.push('/login?error=auth_failed')
      } else {
        router.push('/dashboard')
      }
    }

    handleCallback()
  }, [router])

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary animate-pulse-neon mx-auto mb-4"></div>
        <p className="text-muted-foreground">Completing authentication...</p>
      </div>
    </div>
  )
}
