'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { PasswordInput } from '@/components/ui/password-input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from 'sonner'
import { Shield, Loader2, ArrowLeft, AlertCircle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

export default function AdminLoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const error = searchParams?.get('error')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      toast.error('Veuillez remplir tous les champs')
      return
    }

    setLoading(true)
    try {
      const userData = await login(email, password)
      
      // Vérifier si l'utilisateur est admin
      if (userData.role === 'admin') {
        toast.success('Connexion admin réussie')
        router.push('/admin')
      } else {
        toast.error('Accès refusé: Privilèges administrateur requis')
        // Déconnecter l'utilisateur car ce n'est pas un admin
        router.push('/admin/login?error=not_admin')
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Échec de la connexion'
      toast.error(errorMessage)
      router.push(`/admin/login?error=auth_failed`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      {/* Background effects */}
      <div className="absolute inset-0 grid-texture opacity-30"></div>
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[128px]"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-destructive/10 rounded-full blur-[128px]"></div>

      {/* Bouton retour en haut à gauche */}
      <Link href="/" className="absolute top-6 left-6 z-10">
        <Button
          variant="outline"
          size="sm"
          className="bg-background-paper/80 backdrop-blur-xl border-white/10 hover:border-primary/50"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour à l&apos;accueil
        </Button>
      </Link>

      <Card className="w-full max-w-md relative bg-background-paper/80 backdrop-blur-xl border-white/10">
        <CardHeader className="text-center">
          <div className="inline-flex items-center justify-center gap-2 mb-4">
            <div className="w-12 h-12 rounded-md bg-destructive/20 border border-destructive/50 flex items-center justify-center">
              <Shield className="w-6 h-6 text-destructive" />
            </div>
          </div>
          <CardTitle className="text-2xl font-heading">Admin Access</CardTitle>
          <CardDescription>Connexion administrateur NativiWeb Studio</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Message d'erreur */}
          {error === 'not_admin' && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Accès refusé. Vous devez avoir les privilèges administrateur pour accéder à cette page.
              </AlertDescription>
            </Alert>
          )}
          
          {error === 'auth_failed' && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Échec de l&apos;authentification. Vérifiez vos identifiants.
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="admin-email">Email Administrateur</Label>
              <Input
                id="admin-email"
                type="email"
                placeholder="admin@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-background border-white/10"
                disabled={loading}
                autoComplete="email"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="admin-password">Mot de passe</Label>
              <PasswordInput
                id="admin-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-background border-white/10"
                disabled={loading}
                autoComplete="current-password"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full bg-destructive text-white font-bold hover:bg-destructive/90"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Connexion...
                </>
              ) : (
                <>
                  <Shield className="w-4 h-4 mr-2" />
                  Se connecter en tant qu&apos;administrateur
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-white/10">
            <p className="text-xs text-center text-muted-foreground">
              ⚠️ Cette page est réservée aux administrateurs uniquement.
              <br />
              Toute tentative non autorisée sera enregistrée.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

