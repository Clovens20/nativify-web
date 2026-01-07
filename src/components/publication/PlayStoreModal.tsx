'use client'

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, ExternalLink, Download, AlertCircle, DollarSign, FileText, Image, Shield } from 'lucide-react'

interface PlayStoreModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  buildId?: string
}

export function PlayStoreModal({ open, onOpenChange, buildId }: PlayStoreModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-background-paper border-white/10">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-success/10 flex items-center justify-center">
              <Shield className="w-6 h-6 text-success" />
            </div>
            <div>
              <DialogTitle>Publier sur Google Play Store</DialogTitle>
              <DialogDescription>
                Guide complet pour publier votre application Android
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
                  <DollarSign className="w-5 h-5 text-success mt-0.5" />
                  <div>
                    <h4 className="font-medium mb-1">Compte Google Play Developer</h4>
                    <p className="text-sm text-muted-foreground">
                      Inscription unique : <strong>25$ USD</strong> (frais uniques, pas d'abonnement annuel)
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Accès à vie après paiement, permet de publier un nombre illimité d'applications
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10 bg-background/50">
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-primary mt-0.5" />
                  <div>
                    <h4 className="font-medium mb-1">APK signé</h4>
                    <p className="text-sm text-muted-foreground">
                      Votre APK téléchargé depuis NativiWeb est déjà signé et prêt à être publié
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10 bg-background/50">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-info mt-0.5" />
                  <div>
                    <h4 className="font-medium mb-1">Politique de confidentialité</h4>
                    <p className="text-sm text-muted-foreground">
                      URL publique obligatoire pour toutes les applications qui collectent des données utilisateur
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
                    <h4 className="font-medium mb-1">Créer votre compte développeur</h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      Si vous n'avez pas encore de compte, créez-en un sur Google Play Console
                    </p>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => window.open('https://play.google.com/console/signup', '_blank')}
                      className="bg-success/10 border-success/20 text-success hover:bg-success/20"
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Créer un compte développeur
                    </Button>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10">
                <div className="flex items-start gap-3">
                  <Badge variant="default" className="mt-0.5">2</Badge>
                  <div className="flex-1">
                    <h4 className="font-medium mb-1">Créer une nouvelle application</h4>
                    <p className="text-sm text-muted-foreground">
                      Dans Play Console, allez dans <strong>Créer une application</strong> et remplissez les informations de base
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border border-white/10">
                <div className="flex items-start gap-3">
                  <Badge variant="default" className="mt-0.5">3</Badge>
                  <div className="flex-1">
                    <h4 className="font-medium mb-1">Télécharger votre APK</h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      Téléchargez votre APK depuis NativiWeb, puis allez dans <strong>Production → Créer une version</strong>
                    </p>
                    {buildId && (
                      <a href={`/api/builds/${buildId}/download`} download>
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4 mr-2" />
                          Télécharger APK
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
                    <h4 className="font-medium mb-1">Remplir les informations de la boutique</h4>
                    <p className="text-sm text-muted-foreground">
                      Ajoutez description, screenshots, icône, catégorie et autres métadonnées requises
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
                      Google examinera votre application (généralement 1-3 jours). Vous recevrez un email une fois approuvée
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
                  Minimum 2 screenshots par taille d'écran (phone, tablet, TV)
                </p>
              </div>
              <div className="p-3 rounded-lg border border-white/10 bg-background/50">
                <h4 className="font-medium text-sm mb-1">Icône haute résolution</h4>
                <p className="text-xs text-muted-foreground">
                  512x512 px (PNG, sans transparence)
                </p>
              </div>
              <div className="p-3 rounded-lg border border-white/10 bg-background/50">
                <h4 className="font-medium text-sm mb-1">Description</h4>
                <p className="text-xs text-muted-foreground">
                  Description courte (80 caractères) et longue (4000 caractères)
                </p>
              </div>
              <div className="p-3 rounded-lg border border-white/10 bg-background/50">
                <h4 className="font-medium text-sm mb-1">Politique de confidentialité</h4>
                <p className="text-xs text-muted-foreground">
                  URL publique (requis si l'app collecte des données)
                </p>
              </div>
            </div>
          </section>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-white/10">
            <Button
              onClick={() => window.open('https://play.google.com/console', '_blank')}
              className="flex-1 bg-success hover:bg-success/90"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Ouvrir Play Console
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
                  La première fois que vous publiez une application, Google peut prendre jusqu'à 7 jours pour approuver votre compte développeur. 
                  Les soumissions suivantes sont généralement approuvées en 1-3 jours.
                </p>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

