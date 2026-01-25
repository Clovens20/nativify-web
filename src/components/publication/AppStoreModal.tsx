'use client'

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, ExternalLink, Download, AlertCircle, DollarSign, FileText, Image, Shield, Apple } from 'lucide-react'
import { getBuildBackendUrl } from '@/lib/buildBackend'

interface AppStoreModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  buildId?: string
}

export function AppStoreModal({ open, onOpenChange, buildId }: AppStoreModalProps) {
  const downloadUrl = buildId ? `${getBuildBackendUrl()}/api/builds/${buildId}/download` : undefined

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-background-paper border-white/10">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-info/10 flex items-center justify-center">
              <Apple className="w-6 h-6 text-info" />
            </div>
            <div>
              <DialogTitle>Publier sur Apple App Store</DialogTitle>
              <DialogDescription>
                Guide complet pour publier votre application iOS
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Prérequis */}
          <section>
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-warning" />
              Prérequis nécessaires
            </h3>
            <div className="space-y-3">
              <div className="p-4 rounded-lg border border-white/10 bg-background/50">
                <div className="flex items-start gap-3">
                  <DollarSign className="w-5 h-5 text-info mt-0.5" />
                  <div>
                    <h4 className="font-medium mb-1">Compte Apple Developer Program</h4>
                    <p className="text-sm text-muted-foreground">
                      Abonnement annuel : <strong>99$ USD</strong> (renouvellement annuel requis)
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Nécessaire pour publier sur l'App Store et tester sur des appareils physiques
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10 bg-background/50">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-primary mt-0.5" />
                  <div>
                    <h4 className="font-medium mb-1">Certificats et Provisioning Profiles</h4>
                    <p className="text-sm text-muted-foreground">
                      Votre IPA téléchargé depuis NativiWeb est déjà signé. Vous aurez besoin de configurer les certificats dans App Store Connect
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10 bg-background/50">
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-primary mt-0.5" />
                  <div>
                    <h4 className="font-medium mb-1">Politique de confidentialité</h4>
                    <p className="text-sm text-muted-foreground">
                      URL publique obligatoire pour toutes les applications qui collectent des données utilisateur
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10 bg-background/50">
                <div className="flex items-start gap-3">
                  <Apple className="w-5 h-5 text-info mt-0.5" />
                  <div>
                    <h4 className="font-medium mb-1">App ID et Bundle Identifier</h4>
                    <p className="text-sm text-muted-foreground">
                      Identifiant unique pour votre application (ex: com.votresociete.yourapp)
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Étapes de publication */}
          <section>
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-success" />
              Étapes de publication
            </h3>
            <div className="space-y-4">
              <div className="p-4 rounded-lg border border-white/10">
                <div className="flex items-start gap-3">
                  <Badge variant="default" className="mt-0.5">1</Badge>
                  <div className="flex-1">
                    <h4 className="font-medium mb-1">Rejoindre l'Apple Developer Program</h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      Si vous n'êtes pas encore membre, inscrivez-vous sur developer.apple.com
                    </p>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => window.open('https://developer.apple.com/programs/', '_blank')}
                      className="bg-info/10 border-info/20 text-info hover:bg-info/20"
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Rejoindre le programme développeur
                    </Button>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10">
                <div className="flex items-start gap-3">
                  <Badge variant="default" className="mt-0.5">2</Badge>
                  <div className="flex-1">
                    <h4 className="font-medium mb-1">Créer votre app dans App Store Connect</h4>
                    <p className="text-sm text-muted-foreground">
                      Connectez-vous à App Store Connect et créez une nouvelle application avec un Bundle ID unique
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10">
                <div className="flex items-start gap-3">
                  <Badge variant="default" className="mt-0.5">3</Badge>
                  <div className="flex-1">
                    <h4 className="font-medium mb-1">Télécharger votre IPA</h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      Téléchargez votre IPA depuis NativiWeb, puis utilisez Transporter ou Xcode pour l'uploader
                    </p>
                    {downloadUrl && (
                      <a href={downloadUrl} download>
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4 mr-2" />
                          Télécharger IPA
                        </Button>
                      </a>
                    )}
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10">
                <div className="flex items-start gap-3">
                  <Badge variant="default" className="mt-0.5">4</Badge>
                  <div className="flex-1">
                    <h4 className="font-medium mb-1">Configurer les métadonnées</h4>
                    <p className="text-sm text-muted-foreground">
                      Ajoutez description, screenshots pour chaque taille d'écran, mots-clés, catégorie, et informations de prix
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10">
                <div className="flex items-start gap-3">
                  <Badge variant="default" className="mt-0.5">5</Badge>
                  <div className="flex-1">
                    <h4 className="font-medium mb-1">Soumettre pour révision</h4>
                    <p className="text-sm text-muted-foreground">
                      Apple examinera votre application (généralement 1-7 jours). Vous recevrez des notifications sur l'état de la révision
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Documents requis */}
          <section>
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Image className="w-5 h-5 text-primary" />
              Documents et ressources requis
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3 rounded-lg border border-white/10 bg-background/50">
                <h4 className="font-medium text-sm mb-1">Screenshots</h4>
                <p className="text-xs text-muted-foreground">
                  Requis pour chaque taille d'écran : 6.5", 6.7", 5.5", iPad Pro, etc. (minimum 1 par taille)
                </p>
              </div>
              <div className="p-3 rounded-lg border border-white/10 bg-background/50">
                <h4 className="font-medium text-sm mb-1">Icône App Store</h4>
                <p className="text-xs text-muted-foreground">
                  1024x1024 px (PNG, sans transparence, coins arrondis automatiques)
                </p>
              </div>
              <div className="p-3 rounded-lg border border-white/10 bg-background/50">
                <h4 className="font-medium text-sm mb-1">Description</h4>
                <p className="text-xs text-muted-foreground">
                  Nom (30 caractères), sous-titre (30 caractères), description (4000 caractères)
                </p>
              </div>
              <div className="p-3 rounded-lg border border-white/10 bg-background/50">
                <h4 className="font-medium text-sm mb-1">Politique de confidentialité</h4>
                <p className="text-xs text-muted-foreground">
                  URL publique (requis si l'app collecte des données utilisateur)
                </p>
              </div>
              <div className="p-3 rounded-lg border border-white/10 bg-background/50">
                <h4 className="font-medium text-sm mb-1">Mots-clés</h4>
                <p className="text-xs text-muted-foreground">
                  Maximum 100 caractères, séparés par des virgules (pour le référencement)
                </p>
              </div>
              <div className="p-3 rounded-lg border border-white/10 bg-background/50">
                <h4 className="font-medium text-sm mb-1">Informations de contact</h4>
                <p className="text-xs text-muted-foreground">
                  Email de support, URL de support, informations de marketing (optionnel)
                </p>
              </div>
            </div>
          </section>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-white/10">
            <Button
              onClick={() => window.open('https://appstoreconnect.apple.com', '_blank')}
              className="flex-1 bg-info hover:bg-info/90"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Ouvrir App Store Connect
            </Button>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Fermer
            </Button>
          </div>

          {/* Note importante */}
          <div className="p-4 rounded-lg bg-warning/10 border border-warning/20">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-warning mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium mb-1">Note importante</p>
                <p className="text-muted-foreground">
                  Apple a des directives de révision strictes. Assurez-vous que votre application respecte les 
                  <a href="https://developer.apple.com/app-store/review/guidelines/" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline ml-1">
                    App Store Review Guidelines
                  </a>. 
                  La première soumission peut prendre jusqu'à 7 jours pour être approuvée.
                </p>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

