'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { createClient } from '@/lib/supabase'
import { User, Session } from '@supabase/supabase-js'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL + '/api'

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
    const initAuth = async () => {
      try {
        const { data: { session: currentSession } } = await supabase.auth.getSession()
        
        if (currentSession?.user) {
          setSession(currentSession)
          // Fetch user profile from our backend
          try {
            const response = await axios.get(`${API_URL}/auth/me?token=${currentSession.access_token}`)
            setUser(response.data)
          } catch (error) {
            console.error('Failed to fetch user profile:', error)
            setUser({
              id: currentSession.user.id,
              email: currentSession.user.email || '',
              name: currentSession.user.user_metadata?.name || '',
              role: 'user'
            })
          }
        }
      } catch (error) {
        console.error('Auth init error:', error)
      } finally {
        setLoading(false)
      }
    }

    initAuth()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, newSession) => {
      setSession(newSession)
      if (newSession?.user) {
        try {
          const response = await axios.get(`${API_URL}/auth/me?token=${newSession.access_token}`)
          setUser(response.data)
        } catch (error) {
          setUser({
            id: newSession.user.id,
            email: newSession.user.email || '',
            name: newSession.user.user_metadata?.name || '',
            role: 'user'
          })
        }
      } else {
        setUser(null)
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const login = async (email: string, password: string): Promise<UserProfile> => {
    const response = await axios.post(`${API_URL}/auth/login`, { email, password })
    const { token, user: userData } = response.data
    
    // Also sign in with Supabase client to maintain session
    await supabase.auth.signInWithPassword({ email, password })
    
    setUser(userData)
    return userData
  }

  const register = async (email: string, password: string, name: string) => {
    const response = await axios.post(`${API_URL}/auth/register`, { email, password, name })
    return response.data
  }

  const logout = async () => {
    try {
      if (session?.access_token) {
        await axios.post(`${API_URL}/auth/logout?token=${session.access_token}`)
      }
    } catch (error) {
      console.error('Logout error:', error)
    }
    await supabase.auth.signOut()
    setUser(null)
    setSession(null)
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
