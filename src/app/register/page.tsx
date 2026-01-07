'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { PasswordInput } from '@/components/ui/password-input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { Zap, Github, Loader2 } from 'lucide-react'

export default function RegisterPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { register, loginWithGitHub } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!name || !email || !password || !confirmPassword) {
      toast.error('Please fill in all fields')
      return
    }

    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    if (password.length < 6) {
      toast.error('Password must be at least 6 characters')
      return
    }

    setLoading(true)
    try {
      await register(email, password, name)
      toast.success('Account created! Please sign in.')
      router.push('/login')
    } catch (error: any) {
      // Détecter si c'est une erreur de connexion au backend
      if (error.message?.includes('backend n\'est pas disponible') || error.isConnectionError || error.code === 'ECONNREFUSED') {
        toast.error('Le serveur backend n\'est pas disponible. Veuillez démarrer le serveur avec: npm run dev', {
          duration: 8000
        })
      } else {
        // Afficher un message d'erreur plus détaillé
        const errorMessage = error.message || error.response?.data?.detail || error.response?.data?.message || 'Registration failed'
        console.error('Registration error details:', {
          error,
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        })
        toast.error(errorMessage)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleGitHubLogin = async () => {
    try {
      await loginWithGitHub()
    } catch (error) {
      toast.error('GitHub login failed')
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 sm:p-6">
      {/* Background effects */}
      <div className="absolute inset-0 grid-texture opacity-30"></div>
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[128px]"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/10 rounded-full blur-[128px]"></div>

      <Card className="w-full max-w-md relative bg-background-paper/80 backdrop-blur-xl border-white/10 mx-auto">
        <CardHeader className="text-center">
          <Link href="/" className="inline-flex items-center justify-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-md bg-primary/20 border border-primary flex items-center justify-center">
              <Zap className="w-5 h-5 text-primary" />
            </div>
          </Link>
          <CardTitle className="text-2xl font-heading">Create Account</CardTitle>
          <CardDescription>Get started with NativiWeb Studio</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-background border-white/10"
                data-testid="register-name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-background border-white/10"
                data-testid="register-email"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <PasswordInput
                id="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-background border-white/10"
                data-testid="register-password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <PasswordInput
                id="confirmPassword"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="bg-background border-white/10"
                data-testid="register-confirm-password"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full bg-primary text-black font-bold hover:bg-primary-hover"
              disabled={loading}
              data-testid="register-submit"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating account...
                </>
              ) : (
                'Create Account'
              )}
            </Button>
          </form>

          <div className="relative my-6">
            <Separator />
            <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background-paper px-2 text-xs text-muted-foreground">
              or continue with
            </span>
          </div>

          <Button
            type="button"
            variant="outline"
            className="w-full border-white/10"
            onClick={handleGitHubLogin}
            data-testid="github-register"
          >
            <Github className="w-4 h-4 mr-2" />
            GitHub
          </Button>
        </CardContent>
        <CardFooter className="justify-center">
          <p className="text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link href="/login" className="text-primary hover:underline" data-testid="login-link">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
