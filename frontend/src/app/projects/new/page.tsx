'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { projectsApi } from '@/lib/api'
import { toast } from 'sonner'
import { Loader2, Globe, Smartphone, Apple } from 'lucide-react'

export default function NewProjectPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    web_url: '',
    description: '',
    android: true,
    ios: true
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name || !formData.web_url) {
      toast.error('Please fill in required fields')
      return
    }

    if (!formData.android && !formData.ios) {
      toast.error('Please select at least one platform')
      return
    }

    if (!user?.id) {
      toast.error('You must be logged in')
      return
    }

    setLoading(true)
    try {
      const platform = []
      if (formData.android) platform.push('android')
      if (formData.ios) platform.push('ios')

      const project = await projectsApi.create({
        name: formData.name,
        web_url: formData.web_url,
        description: formData.description,
        platform
      }, user.id)

      toast.success('Project created successfully!')
      router.push(`/projects/${project.id}`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create project')
    } finally {
      setLoading(false)
    }
  }

  return (
    <DashboardLayout title="Create New Project" subtitle="Configure your web app for native deployment">
      <div className="max-w-2xl">
        <Card className="bg-background-paper border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-primary" />
              Project Details
            </CardTitle>
            <CardDescription>Enter your web application details</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">Project Name *</Label>
                <Input
                  id="name"
                  placeholder="My Awesome App"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="bg-background border-white/10"
                  data-testid="project-name"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="web_url">Web App URL *</Label>
                <Input
                  id="web_url"
                  type="url"
                  placeholder="https://myapp.com"
                  value={formData.web_url}
                  onChange={(e) => setFormData({ ...formData, web_url: e.target.value })}
                  className="bg-background border-white/10"
                  data-testid="project-url"
                />
                <p className="text-xs text-muted-foreground">The URL of your web application to convert</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Brief description of your app..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="bg-background border-white/10"
                  data-testid="project-description"
                />
              </div>

              <div className="space-y-4">
                <Label>Target Platforms *</Label>
                <div className="flex gap-6">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="android"
                      checked={formData.android}
                      onCheckedChange={(checked) => setFormData({ ...formData, android: !!checked })}
                      data-testid="platform-android"
                    />
                    <Label htmlFor="android" className="flex items-center gap-2 cursor-pointer">
                      <Smartphone className="w-4 h-4 text-success" />
                      Android
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="ios"
                      checked={formData.ios}
                      onCheckedChange={(checked) => setFormData({ ...formData, ios: !!checked })}
                      data-testid="platform-ios"
                    />
                    <Label htmlFor="ios" className="flex items-center gap-2 cursor-pointer">
                      <Apple className="w-4 h-4 text-info" />
                      iOS
                    </Label>
                  </div>
                </div>
              </div>

              <div className="flex gap-4 pt-4">
                <Button
                  type="submit"
                  className="bg-primary text-black font-bold hover:bg-primary-hover"
                  disabled={loading}
                  data-testid="create-project-submit"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Project'
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="border-white/10"
                  onClick={() => router.back()}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
