'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import { logger } from '@/lib/logger'

export default function AuthCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const handleCallback = async () => {
      const supabase = createClient()
      
      // Handle the OAuth callback
      const code = searchParams.get('code')
      if (code) {
        const { error } = await supabase.auth.exchangeCodeForSession(code)
        
        if (error) {
          logger.error('Auth callback error', error, { context: 'oauth_callback' })
          router.push('/login?error=auth_failed')
        } else {
          router.push('/dashboard')
        }
      } else {
        // Try to get session from hash
        const { data: { session }, error } = await supabase.auth.getSession()
        if (error || !session) {
          router.push('/login?error=auth_failed')
        } else {
          router.push('/dashboard')
        }
      }
    }

    handleCallback()
  }, [router, searchParams])

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary animate-pulse-neon mx-auto mb-4"></div>
        <p className="text-muted-foreground">Completing authentication...</p>
      </div>
    </div>
  )
}
