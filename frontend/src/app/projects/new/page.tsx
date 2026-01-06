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
import { Badge } from '@/components/ui/badge'
import { projectsApi } from '@/lib/api'
import { toast } from 'sonner'
import { 
  Loader2, 
  Globe, 
  Smartphone, 
  Apple,
  ShoppingCart,
  FileText,
  Briefcase,
  Gamepad2,
  GraduationCap,
  Utensils,
  Check
} from 'lucide-react'

const templates = [
  {
    id: 'blank',
    name: 'Projet Vide',
    description: 'Commencez de zéro avec une configuration minimale',
    icon: Globe,
    color: 'primary',
    features: ['push_notifications', 'local_storage'],
    recommended: false
  },
  {
    id: 'pwa',
    name: 'PWA Standard',
    description: 'Progressive Web App avec toutes les fonctionnalités essentielles',
    icon: Smartphone,
    color: 'success',
    features: ['push_notifications', 'local_storage', 'geolocation', 'camera', 'share'],
    recommended: true
  },
  {
    id: 'ecommerce',
    name: 'E-Commerce',
    description: 'Boutique en ligne avec paiements et notifications',
    icon: ShoppingCart,
    color: 'warning',
    features: ['push_notifications', 'local_storage', 'biometrics', 'haptics', 'share', 'clipboard'],
    recommended: false
  },
  {
    id: 'blog',
    name: 'Blog / Media',
    description: 'Site de contenu avec partage social et offline',
    icon: FileText,
    color: 'info',
    features: ['push_notifications', 'local_storage', 'share', 'clipboard', 'deep_links'],
    recommended: false
  },
  {
    id: 'business',
    name: 'App Business',
    description: 'Application professionnelle avec authentification sécurisée',
    icon: Briefcase,
    color: 'secondary',
    features: ['push_notifications', 'local_storage', 'biometrics', 'contacts', 'file_system', 'clipboard'],
    recommended: false
  },
  {
    id: 'gaming',
    name: 'Jeu / Divertissement',
    description: 'Application ludique avec feedback haptique',
    icon: Gamepad2,
    color: 'destructive',
    features: ['push_notifications', 'local_storage', 'haptics', 'share', 'app_badge'],
    recommended: false
  },
  {
    id: 'education',
    name: 'Éducation',
    description: 'Plateforme d\'apprentissage avec contenu offline',
    icon: GraduationCap,
    color: 'primary',
    features: ['push_notifications', 'local_storage', 'camera', 'file_system', 'share'],
    recommended: false
  },
  {
    id: 'restaurant',
    name: 'Restaurant / Livraison',
    description: 'Application de commande avec géolocalisation',
    icon: Utensils,
    color: 'warning',
    features: ['push_notifications', 'local_storage', 'geolocation', 'share', 'haptics', 'deep_links'],
    recommended: false
  }
]

export default function NewProjectPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    name: '',
    web_url: '',
    description: '',
    android: true,
    ios: true
  })

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplate(templateId)
  }

  const handleNext = () => {
    if (!selectedTemplate) {
      toast.error('Veuillez sélectionner un template')
      return
    }
    setStep(2)
  }

  const handleBack = () => {
    setStep(1)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name || !formData.web_url) {
      toast.error('Veuillez remplir les champs obligatoires')
      return
    }

    if (!formData.android && !formData.ios) {
      toast.error('Veuillez sélectionner au moins une plateforme')
      return
    }

    if (!user?.id) {
      toast.error('Vous devez être connecté')
      return
    }

    setLoading(true)
    try {
      const platform = []
      if (formData.android) platform.push('android')
      if (formData.ios) platform.push('ios')

      const template = templates.find(t => t.id === selectedTemplate)
      const features = template?.features.map(f => ({
        id: f,
        name: f.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        enabled: true,
        config: {}
      })) || []

      const project = await projectsApi.create({
        name: formData.name,
        web_url: formData.web_url,
        description: formData.description || `Projet créé avec le template "${template?.name}"`,
        platform,
        features
      }, user.id)

      toast.success('Projet créé avec succès!')
      router.push(`/projects/${project.id}`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la création')
    } finally {
      setLoading(false)
    }
  }

  const getColorClass = (color: string, type: 'bg' | 'border' | 'text') => {
    const colors: Record<string, Record<string, string>> = {
      primary: { bg: 'bg-primary/10', border: 'border-primary/30', text: 'text-primary' },
      success: { bg: 'bg-success/10', border: 'border-success/30', text: 'text-success' },
      warning: { bg: 'bg-warning/10', border: 'border-warning/30', text: 'text-warning' },
      info: { bg: 'bg-info/10', border: 'border-info/30', text: 'text-info' },
      secondary: { bg: 'bg-secondary/10', border: 'border-secondary/30', text: 'text-secondary' },
      destructive: { bg: 'bg-destructive/10', border: 'border-destructive/30', text: 'text-destructive' }
    }
    return colors[color]?.[type] || colors.primary[type]
  }

  return (
    <DashboardLayout 
      title="Créer un Nouveau Projet" 
      subtitle={step === 1 ? "Choisissez un template pour démarrer rapidement" : "Configurez votre projet"}
    >
      {/* Progress indicator */}
      <div className="flex items-center gap-4 mb-8">
        <div className={`flex items-center gap-2 ${step >= 1 ? 'text-primary' : 'text-muted-foreground'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-primary text-black' : 'bg-muted'}`}>
            {step > 1 ? <Check className="w-4 h-4" /> : '1'}
          </div>
          <span className="font-medium">Template</span>
        </div>
        <div className="h-px w-16 bg-white/10"></div>
        <div className={`flex items-center gap-2 ${step >= 2 ? 'text-primary' : 'text-muted-foreground'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-primary text-black' : 'bg-muted'}`}>
            2
          </div>
          <span className="font-medium">Configuration</span>
        </div>
      </div>

      {/* Step 1: Template Selection */}
      {step === 1 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {templates.map((template) => {
              const Icon = template.icon
              const isSelected = selectedTemplate === template.id
              return (
                <Card 
                  key={template.id}
                  className={`cursor-pointer transition-all hover:scale-[1.02] ${
                    isSelected 
                      ? 'bg-primary/10 border-primary ring-2 ring-primary' 
                      : 'bg-background-paper border-white/10 hover:border-white/20'
                  }`}
                  onClick={() => handleTemplateSelect(template.id)}
                  data-testid={`template-${template.id}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className={`w-10 h-10 rounded-lg ${getColorClass(template.color, 'bg')} ${getColorClass(template.color, 'border')} border flex items-center justify-center`}>
                        <Icon className={`w-5 h-5 ${getColorClass(template.color, 'text')}`} />
                      </div>
                      {template.recommended && (
                        <Badge className="bg-success/20 text-success text-xs">Recommandé</Badge>
                      )}
                      {isSelected && (
                        <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                          <Check className="w-4 h-4 text-black" />
                        </div>
                      )}
                    </div>
                    <h3 className="font-heading font-bold mb-1">{template.name}</h3>
                    <p className="text-xs text-muted-foreground mb-3">{template.description}</p>
                    <div className="flex flex-wrap gap-1">
                      {template.features.slice(0, 3).map(f => (
                        <Badge key={f} variant="outline" className="text-xs">
                          {f.replace(/_/g, ' ')}
                        </Badge>
                      ))}
                      {template.features.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{template.features.length - 3}
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          <div className="flex justify-end">
            <Button 
              onClick={handleNext}
              className="bg-primary text-black font-bold hover:bg-primary-hover"
              disabled={!selectedTemplate}
              data-testid="next-step-btn"
            >
              Continuer
            </Button>
          </div>
        </>
      )}

      {/* Step 2: Project Configuration */}
      {step === 2 && (
        <div className="max-w-2xl">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-primary" />
                Détails du Projet
              </CardTitle>
              <CardDescription>
                Template sélectionné: <span className="text-primary font-medium">
                  {templates.find(t => t.id === selectedTemplate)?.name}
                </span>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="name">Nom du Projet *</Label>
                  <Input
                    id="name"
                    placeholder="Mon Application"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="bg-background border-white/10"
                    data-testid="project-name"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="web_url">URL de l'Application Web *</Label>
                  <Input
                    id="web_url"
                    type="url"
                    placeholder="https://monapp.com"
                    value={formData.web_url}
                    onChange={(e) => setFormData({ ...formData, web_url: e.target.value })}
                    className="bg-background border-white/10"
                    data-testid="project-url"
                  />
                  <p className="text-xs text-muted-foreground">L'URL de votre application web à convertir</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Décrivez brièvement votre application..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="bg-background border-white/10"
                    data-testid="project-description"
                  />
                </div>

                <div className="space-y-4">
                  <Label>Plateformes Cibles *</Label>
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

                {/* Features preview */}
                <div className="space-y-2">
                  <Label>Fonctionnalités incluses</Label>
                  <div className="flex flex-wrap gap-2 p-4 rounded-lg border border-white/10 bg-background">
                    {templates.find(t => t.id === selectedTemplate)?.features.map(f => (
                      <Badge key={f} className="bg-primary/20 text-primary">
                        <Check className="w-3 h-3 mr-1" />
                        {f.replace(/_/g, ' ')}
                      </Badge>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Vous pourrez modifier ces fonctionnalités après la création du projet
                  </p>
                </div>

                <div className="flex gap-4 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    className="border-white/10"
                    onClick={handleBack}
                  >
                    Retour
                  </Button>
                  <Button
                    type="submit"
                    className="bg-primary text-black font-bold hover:bg-primary-hover flex-1"
                    disabled={loading}
                    data-testid="create-project-submit"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Création...
                      </>
                    ) : (
                      'Créer le Projet'
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </DashboardLayout>
  )
}
