'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { Loader2, User, Mail, Shield } from 'lucide-react'

export default function SettingsPage() {
  const { user, loading: authLoading, logout } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <DashboardLayout title="Settings" subtitle="Manage your account settings">
      <div className="max-w-2xl space-y-6">
        {/* Profile Settings */}
        <Card className="bg-background-paper border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5 text-primary" />
              Profile Information
            </CardTitle>
            <CardDescription>Your personal account details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input
                value={user.name}
                disabled
                className="bg-background border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                value={user.email}
                disabled
                className="bg-background border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>Role</Label>
              <Input
                value={user.role}
                disabled
                className="bg-background border-white/10"
              />
            </div>
          </CardContent>
        </Card>

        {/* Account Actions */}
        <Card className="bg-background-paper border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Account Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium">Sign Out</p>
                <p className="text-sm text-muted-foreground">Sign out of your account</p>
              </div>
              <Button 
                variant="outline" 
                className="border-white/10"
                onClick={() => {
                  logout()
                  router.push('/')
                }}
              >
                Sign Out
              </Button>
            </div>
            
            <Separator className="bg-white/10" />
            
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="font-medium text-destructive">Delete Account</p>
                <p className="text-sm text-muted-foreground">Permanently delete your account and all data</p>
              </div>
              <Button 
                variant="destructive"
                onClick={() => toast.error('Account deletion is disabled in demo mode')}
              >
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
