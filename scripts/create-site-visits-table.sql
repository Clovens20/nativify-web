-- Script SQL pour créer la table de tracking des visites du site
-- Exécutez cette requête dans Supabase SQL Editor

-- Table des visites du site
CREATE TABLE IF NOT EXISTS public.site_visits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  page_path TEXT NOT NULL,
  user_agent TEXT,
  referrer TEXT,
  ip_address TEXT,
  country TEXT,
  city TEXT,
  device_type TEXT, -- 'desktop', 'mobile', 'tablet'
  browser TEXT,
  os TEXT,
  session_id TEXT,
  user_id UUID REFERENCES public.users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_site_visits_created_at ON public.site_visits(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_site_visits_page_path ON public.site_visits(page_path);
CREATE INDEX IF NOT EXISTS idx_site_visits_user_id ON public.site_visits(user_id);
CREATE INDEX IF NOT EXISTS idx_site_visits_session_id ON public.site_visits(session_id);
CREATE INDEX IF NOT EXISTS idx_site_visits_device_type ON public.site_visits(device_type);

-- RLS (Row Level Security)
ALTER TABLE public.site_visits ENABLE ROW LEVEL SECURITY;

-- Policy: Tout le monde peut insérer des visites (pour le tracking)
CREATE POLICY "Anyone can track visits"
  ON public.site_visits
  FOR INSERT
  WITH CHECK (true);

-- Policy: Seuls les admins peuvent lire les statistiques
CREATE POLICY "Only admins can view visit stats"
  ON public.site_visits
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.users
      WHERE users.id = auth.uid()
      AND users.role = 'admin'
    )
  );

-- Fonction pour obtenir les statistiques agrégées
CREATE OR REPLACE FUNCTION get_visit_stats()
RETURNS TABLE (
  total_visits BIGINT,
  unique_visitors BIGINT,
  visits_today BIGINT,
  visits_this_week BIGINT,
  visits_this_month BIGINT,
  top_pages JSONB,
  device_breakdown JSONB,
  visits_by_day JSONB
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    (SELECT COUNT(*) FROM public.site_visits) as total_visits,
    (SELECT COUNT(DISTINCT session_id) FROM public.site_visits) as unique_visitors,
    (SELECT COUNT(*) FROM public.site_visits WHERE created_at >= CURRENT_DATE) as visits_today,
    (SELECT COUNT(*) FROM public.site_visits WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as visits_this_week,
    (SELECT COUNT(*) FROM public.site_visits WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as visits_this_month,
    (
      SELECT jsonb_agg(jsonb_build_object('path', page_path, 'count', cnt))
      FROM (
        SELECT page_path, COUNT(*) as cnt
        FROM public.site_visits
        GROUP BY page_path
        ORDER BY cnt DESC
        LIMIT 10
      ) top_pages_subquery
    ) as top_pages,
    (
      SELECT jsonb_object_agg(COALESCE(device_type, 'unknown'), cnt)
      FROM (
        SELECT device_type, COUNT(*) as cnt
        FROM public.site_visits
        GROUP BY device_type
      ) device_subquery
    ) as device_breakdown,
    (
      SELECT jsonb_object_agg(date_trunc('day', created_at)::text, cnt)
      FROM (
        SELECT created_at, COUNT(*) as cnt
        FROM public.site_visits
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY date_trunc('day', created_at)
        ORDER BY date_trunc('day', created_at)
      ) daily_subquery
    ) as visits_by_day;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Vérifier que la table est créée
SELECT 'Table site_visits créée avec succès!' as status;

