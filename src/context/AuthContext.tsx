'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { createClient } from '@/lib/supabase'
import { User, Session } from '@supabase/supabase-js'
import axios from 'axios'
import { logger } from '@/lib/logger'

// In development, use relative URL (proxied by Next.js)
// In production, use absolute URL from env variable
const API_URL = process.env.NODE_ENV === 'production'
  ? (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000') + '/api'
  : '/api'

interface UserProfile {
  id: string
  email: string
  name: string
  role: string
}

interface AuthContextType {
  user: UserProfile | null
  session: Session | null
  loading: boolean
  login: (email: string, password: string) => Promise<UserProfile>
  register: (email: string, password: string, name: string) => Promise<any>
  logout: () => Promise<void>
  loginWithGitHub: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const supabase = createClient()

  useEffect(() => {
    let mounted = true
    
    const initAuth = async () => {
      try {
        const { data: { session: currentSession }, error: sessionError } = await supabase.auth.getSession()
        
        if (sessionError) {
          logger.error('Session error', sessionError, { context: 'initAuth' })
          // Si erreur de session, nettoyer et forcer logout
          await supabase.auth.signOut()
          if (mounted) {
            setUser(null)
            setSession(null)
            setLoading(false)
          }
          return
        }
        
        if (currentSession?.user && mounted) {
          const userEmail = currentSession.user.email
          logger.info('Initializing session', { email: userEmail })
          
          setSession(currentSession)
          
          // Fetch user profile from our backend
          try {
            const response = await axios.get(`${API_URL}/auth/me`, {
              headers: {
                Authorization: `Bearer ${currentSession.access_token}`
              },
              timeout: 15000 // 15 secondes pour laisser le temps au backend
            })
            
            // Vérifier que l'email correspond bien
            if (response.data?.email && response.data.email !== userEmail) {
              logger.warn('Email mismatch', { sessionEmail: userEmail, backendEmail: response.data.email })
              // Forcer logout et nettoyer
              await supabase.auth.signOut()
              if (mounted) {
                setUser(null)
                setSession(null)
              }
              return
            }
            
            if (mounted) {
              setUser(response.data)
            }
          } catch (error: any) {
            // Ne pas afficher d'erreur si c'est juste une erreur de connexion (backend non démarré)
            if (error.code !== 'ECONNREFUSED' && !error.message?.includes('Network Error') && !error.message?.includes('ERR_CONNECTION_REFUSED')) {
              logger.error('Failed to fetch user profile', error, { email: userEmail })
            }
            // Utiliser les données Supabase comme fallback
            if (mounted) {
              setUser({
                id: currentSession.user.id,
                email: userEmail || '',
                name: currentSession.user.user_metadata?.name || '',
                role: 'user'
              })
            }
          }
        } else if (mounted) {
          setUser(null)
          setSession(null)
        }
      } catch (error) {
        logger.error('Init error', error, { context: 'initAuth' })
        if (mounted) {
          setUser(null)
          setSession(null)
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    initAuth()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, newSession) => {
      // Éviter les boucles : ignorer les événements si on est en train de se déconnecter
      if (!mounted) return
      
      logger.debug('Auth state changed', { event, email: newSession?.user?.email })
      
      // Si c'est un SIGNED_OUT, nettoyer immédiatement
      if (event === 'SIGNED_OUT' || !newSession) {
        if (mounted) {
          setSession(null)
          setUser(null)
        }
        return
      }
      
      // Ignorer les événements TOKEN_REFRESHED si l'utilisateur est le même (pour éviter les boucles)
      if (event === 'TOKEN_REFRESHED') {
        const currentUserId = session?.user?.id
        const newUserId = newSession?.user?.id
        
        if (currentUserId && newUserId && currentUserId === newUserId) {
          // Même utilisateur, juste mettre à jour la session
          if (mounted) {
            setSession(newSession)
          }
          return
        }
      }
      
      // Pour SIGNED_IN ou USER_UPDATED, vérifier l'email
      if (newSession?.user && mounted) {
        const newUserEmail = newSession.user.email
        const currentUserEmail = user?.email
        
        // Si on a déjà un utilisateur connecté et que l'email est différent, ne pas changer automatiquement
        if (currentUserEmail && currentUserEmail !== newUserEmail && event !== 'TOKEN_REFRESHED') {
          logger.warn('User switch detected - ignoring', { current: currentUserEmail, new: newUserEmail, event })
          // Ne pas changer, garder l'utilisateur actuel
          return
        }
        
        // Mettre à jour la session
        if (mounted) {
          setSession(newSession)
        }
        
        // Récupérer les informations utilisateur depuis le backend
        try {
          const response = await axios.get(`${API_URL}/auth/me`, {
            headers: {
              Authorization: `Bearer ${newSession.access_token}`
            },
            timeout: 15000 // 15 secondes pour laisser le temps au backend
          })
          
          // Vérifier que l'email correspond
          if (response.data?.email && response.data.email !== newUserEmail) {
            logger.warn('Email mismatch in state change', { sessionEmail: newUserEmail, backendEmail: response.data.email, event })
            // Ne pas forcer logout, juste logger
          }
          
          if (mounted && response.data) {
            setUser(response.data)
          }
        } catch (error: any) {
          // Si erreur 401, ne pas utiliser le fallback (pour éviter les boucles)
          if (error.response?.status === 401) {
            logger.warn('401 error when fetching user profile - keeping current user', { email: newUserEmail, event })
            // Ne pas changer l'utilisateur si on a une erreur 401
            return
          }
          
          // Utiliser les données Supabase comme fallback uniquement si backend non disponible
          if (error.code === 'ECONNREFUSED' || error.isConnectionError) {
            const userMetadata = newSession.user.user_metadata || {}
            const userRole = userMetadata.role || 'user'
            if (mounted) {
              setUser({
                id: newSession.user.id,
                email: newUserEmail || '',
                name: newSession.user.user_metadata?.name || '',
                role: userRole
              })
            }
          }
        }
      }
    })

    return () => {
      mounted = false
      subscription.unsubscribe()
    }
  }, []) // Pas de dépendances - on ne veut initialiser qu'une fois

  const login = async (email: string, password: string): Promise<UserProfile> => {
    try {
      // Vérifier s'il y a déjà une session active avec un autre utilisateur
      const { data: { session: existingSession } } = await supabase.auth.getSession()
      if (existingSession?.user && existingSession.user.email !== email) {
        logger.info('Logging out previous user', { previousEmail: existingSession.user.email, newEmail: email })
        // Nettoyer la session précédente
        await supabase.auth.signOut({ scope: 'global' })
        // Nettoyer le localStorage
        if (typeof window !== 'undefined') {
          Object.keys(localStorage).forEach(key => {
            if (key.startsWith('sb-')) {
              localStorage.removeItem(key)
            }
          })
        }
        // Attendre un peu pour s'assurer que le logout est complété
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      
      logger.info('Logging in user', { email })
      
      const response = await axios.post(`${API_URL}/auth/login`, { email, password }, { timeout: 10000 })
      const { token, user: userData } = response.data
      
      // Vérifier que l'email correspond
      if (userData?.email && userData.email !== email) {
        throw new Error('Email mismatch in login response')
      }
      
      // Sign in with Supabase client to maintain session
      const { data: supabaseAuth, error: supabaseError } = await supabase.auth.signInWithPassword({ email, password })
      
      if (supabaseError) {
        logger.error('Supabase login error', supabaseError, { email })
        throw new Error('Failed to establish session')
      }
      
      // Vérifier que l'email de la session Supabase correspond
      if (supabaseAuth?.user?.email !== email) {
        logger.error('Email mismatch after Supabase login', undefined, { expected: email, actual: supabaseAuth?.user?.email })
        await supabase.auth.signOut()
        throw new Error('Session email mismatch')
      }
      
      setUser(userData)
      return userData
    } catch (error: any) {
      logger.error('Login error', error, { email })
      if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.message?.includes('ERR_CONNECTION_REFUSED') || error.isConnectionError) {
        throw new Error('Le serveur backend n\'est pas disponible. Veuillez démarrer le serveur avec: npm run dev')
      }
      throw error
    }
  }

  const register = async (email: string, password: string, name: string) => {
    try {
      const response = await axios.post(`${API_URL}/auth/register`, { email, password, name })
      return response.data
    } catch (error: any) {
      // Log detailed error for debugging
      logger.error('Registration error', error, {
        response: error.response?.data,
        status: error.response?.status,
        url: `${API_URL}/auth/register`,
        backendUrl: process.env.NEXT_PUBLIC_BACKEND_URL
      })
      
      // Re-throw with more context
      if (error.response) {
        // Server responded with error
        throw new Error(error.response.data?.detail || error.response.data?.message || 'Registration failed')
      } else if (error.request) {
        // Request made but no response (backend not running or CORS issue)
        const backendUrl = typeof window !== 'undefined' && process.env.NODE_ENV === 'production'
          ? (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000')
          : 'http://localhost:8000'
        throw new Error('Cannot connect to server. Please make sure the backend is running on ' + backendUrl)
      } else {
        // Error setting up request
        throw new Error(error.message || 'Registration failed')
      }
    }
  }

  const logout = async () => {
    try {
      logger.info('Logging out user', { email: user?.email })
      
      // Nettoyer d'abord l'état local
      setUser(null)
      setSession(null)
      
      // Ensuite appeler les APIs de logout
      if (session?.access_token) {
        try {
          await axios.post(`${API_URL}/auth/logout`, {}, {
            headers: {
              Authorization: `Bearer ${session.access_token}`
            },
            timeout: 3000
          })
        } catch (error) {
          logger.error('Backend logout error (ignored)', error, { email: user?.email })
        }
      }
      
      // Nettoyer complètement la session Supabase
      await supabase.auth.signOut({ scope: 'global' })
      
      // Nettoyer aussi le storage manuellement pour être sûr
      if (typeof window !== 'undefined') {
        // Nettoyer toutes les clés Supabase du localStorage
        Object.keys(localStorage).forEach(key => {
          if (key.startsWith('sb-')) {
            localStorage.removeItem(key)
          }
        })
      }
    } catch (error) {
      logger.error('Logout error', error, { email: user?.email })
      // Forcer le nettoyage même en cas d'erreur
      setUser(null)
      setSession(null)
    }
  }

  const loginWithGitHub = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'github',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    })
  }

  const value: AuthContextType = {
    user,
    session,
    loading,
    login,
    register,
    logout,
    loginWithGitHub,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
