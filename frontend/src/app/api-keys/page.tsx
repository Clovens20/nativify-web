'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { apiKeysApi } from '@/lib/api'
import { toast } from 'sonner'
import { 
  Key, 
  Plus, 
  Copy, 
  Trash2,
  Eye,
  EyeOff,
  Loader2
} from 'lucide-react'

interface APIKey {
  id: string
  name: string
  key: string
  permissions: string[]
  last_used: string | null
  created_at: string
}

export default function ApiKeysPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [apiKeys, setApiKeys] = useState<APIKey[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    const fetchApiKeys = async () => {
      if (!user?.id) return
      try {
        const data = await apiKeysApi.getAll(user.id)
        setApiKeys(data)
      } catch (error) {
        console.error('Failed to fetch API keys:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchApiKeys()
  }, [user])

  const handleCreateKey = async () => {
    if (!newKeyName.trim() || !user?.id) return
    
    setCreating(true)
    try {
      const newKey = await apiKeysApi.create({ name: newKeyName, permissions: ['read', 'write'] }, user.id)
      setApiKeys([newKey, ...apiKeys])
      setNewKeyName('')
      setDialogOpen(false)
      toast.success('API key created')
    } catch (error) {
      toast.error('Failed to create API key')
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteKey = async (keyId: string) => {
    if (!user?.id) return
    if (!confirm('Are you sure you want to delete this API key?')) return
    
    try {
      await apiKeysApi.delete(keyId, user.id)
      setApiKeys(apiKeys.filter(k => k.id !== keyId))
      toast.success('API key deleted')
    } catch (error) {
      toast.error('Failed to delete API key')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const toggleKeyVisibility = (keyId: string) => {
    const newVisible = new Set(visibleKeys)
    if (newVisible.has(keyId)) {
      newVisible.delete(keyId)
    } else {
      newVisible.add(keyId)
    }
    setVisibleKeys(newVisible)
  }

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <DashboardLayout title="API Keys" subtitle="Manage your API keys for SDK integration">
      <div className="flex justify-end mb-6">
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-primary text-black font-bold hover:bg-primary-hover" data-testid="create-api-key-btn">
              <Plus className="w-4 h-4 mr-2" />
              Create API Key
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-background-paper border-white/10">
            <DialogHeader>
              <DialogTitle>Create New API Key</DialogTitle>
              <DialogDescription>
                Create a new API key for SDK integration
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="keyName">Key Name</Label>
              <Input
                id="keyName"
                placeholder="Production Key"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                className="bg-background border-white/10 mt-2"
                data-testid="api-key-name-input"
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)} className="border-white/10">
                Cancel
              </Button>
              <Button 
                onClick={handleCreateKey} 
                disabled={!newKeyName.trim() || creating}
                className="bg-primary text-black"
                data-testid="create-api-key-submit"
              >
                {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="bg-background-paper border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="w-5 h-5 text-primary" />
            Your API Keys
          </CardTitle>
          <CardDescription>Use these keys to authenticate your SDK</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-20">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <Key className="w-8 h-8 text-primary" />
              </div>
              <p className="text-muted-foreground">No API keys yet</p>
              <p className="text-sm text-muted-foreground mt-1">Create your first API key to get started</p>
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys.map((apiKey) => (
                <div
                  key={apiKey.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-white/10"
                  data-testid={`api-key-${apiKey.id}`}
                >
                  <div className="flex-1">
                    <p className="font-medium">{apiKey.name}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <code className="text-sm bg-background px-3 py-1 rounded border border-white/10 font-mono">
                        {visibleKeys.has(apiKey.id) ? apiKey.key : '••••••••••••••••••••••••'}
                      </code>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => toggleKeyVisibility(apiKey.id)}
                        className="h-8 w-8"
                      >
                        {visibleKeys.has(apiKey.id) ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => copyToClipboard(apiKey.key)}
                        className="h-8 w-8"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      {apiKey.permissions.map((perm) => (
                        <Badge key={perm} variant="outline" className="text-xs">
                          {perm}
                        </Badge>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      Created: {new Date(apiKey.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-destructive"
                    onClick={() => handleDeleteKey(apiKey.id)}
                    data-testid={`delete-api-key-${apiKey.id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </DashboardLayout>
  )
}
