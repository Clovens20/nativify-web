-- Script SQL pour créer la table templates dans Supabase
-- Exécutez cette requête dans Supabase SQL Editor

-- Table des templates de projets
CREATE TABLE IF NOT EXISTS public.templates (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  features TEXT[] DEFAULT ARRAY[]::TEXT[],
  recommended BOOLEAN DEFAULT FALSE,
  icon TEXT,
  color TEXT DEFAULT 'primary',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_templates_recommended ON public.templates(recommended);
CREATE INDEX IF NOT EXISTS idx_templates_created_at ON public.templates(created_at DESC);

-- RLS (Row Level Security) - Les templates sont publics en lecture, admin seulement en écriture
ALTER TABLE public.templates ENABLE ROW LEVEL SECURITY;

-- Policy: Tout le monde peut lire les templates
CREATE POLICY "Templates are viewable by everyone"
  ON public.templates
  FOR SELECT
  USING (true);

-- Policy: Seuls les admins peuvent insérer/modifier/supprimer
CREATE POLICY "Only admins can manage templates"
  ON public.templates
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.users
      WHERE users.id = auth.uid()
      AND users.role = 'admin'
    )
  );

-- Insérer les templates par défaut
INSERT INTO public.templates (id, name, description, features, recommended, icon, color) VALUES
('blank', 'Projet Vide', 'Commencez de zéro avec une configuration minimale', ARRAY['push_notifications', 'local_storage'], FALSE, 'globe', 'primary'),
('pwa', 'PWA Standard', 'Progressive Web App avec toutes les fonctionnalités essentielles', ARRAY['push_notifications', 'local_storage', 'geolocation', 'camera', 'share'], TRUE, 'smartphone', 'success'),
('ecommerce', 'E-Commerce', 'Boutique en ligne avec paiements et notifications', ARRAY['push_notifications', 'local_storage', 'biometrics', 'haptics', 'share', 'clipboard'], FALSE, 'shopping-cart', 'warning'),
('blog', 'Blog / Media', 'Site de contenu avec partage social et offline', ARRAY['push_notifications', 'local_storage', 'share', 'clipboard', 'deep_links'], FALSE, 'file-text', 'info'),
('business', 'App Business', 'Application professionnelle avec authentification sécurisée', ARRAY['push_notifications', 'local_storage', 'biometrics', 'contacts', 'file_system', 'clipboard'], FALSE, 'briefcase', 'secondary'),
('gaming', 'Jeu / Divertissement', 'Application ludique avec feedback haptique', ARRAY['push_notifications', 'local_storage', 'haptics', 'share', 'app_badge'], FALSE, 'gamepad', 'destructive')
ON CONFLICT (id) DO NOTHING;

-- Vérifier les templates créés
SELECT id, name, description, recommended, created_at
FROM public.templates
ORDER BY created_at ASC;

