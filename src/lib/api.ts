import axios from 'axios';
import { createClient } from './supabase';
import { apiCache } from './api-cache';
import { logger } from './logger';

// In development, use relative URL (proxied by Next.js)
// In production, use absolute URL from env variable
const API_URL = process.env.NODE_ENV === 'production' 
  ? (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000') + '/api'
  : '/api';

// Create axios instance with interceptor to add auth token
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 secondes de timeout (augmenté pour éviter les timeouts)
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const supabase = createClient();
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();
      
      if (sessionError) {
        logger.error('[API] Error getting session', sessionError, { url: config.url });
        // Ne pas bloquer la requête, continuer sans token
        return config;
      }
      
      if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
      } else {
        logger.debug('[API] No access token found in session', { url: config.url });
      }
    } catch (error) {
      logger.error('[API] Failed to get session in interceptor', error, { url: config.url });
      // Ne pas bloquer la requête en cas d'erreur
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle errors gracefully
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Gérer les erreurs de connexion
    if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.message?.includes('ERR_CONNECTION_REFUSED')) {
      const backendUrl = typeof window !== 'undefined' && process.env.NODE_ENV === 'production'
        ? (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000')
        : 'http://localhost:8000';
      logger.warn('[API] Backend non disponible', { backendUrl, url: error.config?.url });
      
      const customError = new Error('Le serveur backend n\'est pas disponible. Veuillez démarrer le serveur avec: npm run dev');
      (customError as any).isConnectionError = true;
      (customError as any).backendUrl = backendUrl;
      return Promise.reject(customError);
    }
    
    // Gérer les erreurs 401 (Unauthorized) - NE PAS déconnecter automatiquement
    if (error.response?.status === 401) {
      logger.warn('[API] Unauthorized request', {
        url: error.config?.url,
        status: 401,
        message: error.response?.data?.detail || 'Unauthorized'
      });
      
      // Ne pas déconnecter automatiquement, juste logger l'erreur
      // L'application décidera si une déconnexion est nécessaire
    }
    
    // Gérer les erreurs 403 (Forbidden)
    if (error.response?.status === 403) {
      logger.warn('[API] Forbidden request', {
        url: error.config?.url,
        status: 403,
        message: error.response?.data?.detail || 'Forbidden'
      });
    }
    
    return Promise.reject(error);
  }
);

// Projects API avec cache pour améliorer les performances
export const projectsApi = {
  getAll: async (useCache: boolean = true) => {
    const cacheKey = 'projects:all';
    
    // Vérifier le cache
    if (useCache) {
      const cached = apiCache.get(cacheKey);
      if (cached) {
        return cached;
      }
    }
    
    const response = await apiClient.get('/projects');
    const data = response.data;
    
    // Mettre en cache (TTL: 2 minutes)
    if (useCache) {
      apiCache.set(cacheKey, data, 2 * 60 * 1000);
    }
    
    return data;
  },
  
  getOne: async (projectId: string, useCache: boolean = true) => {
    const cacheKey = `projects:${projectId}`;
    
    // Vérifier le cache
    if (useCache) {
      const cached = apiCache.get(cacheKey);
      if (cached) {
        return cached;
      }
    }
    
    const response = await apiClient.get(`/projects/${projectId}`);
    const data = response.data;
    
    // Mettre en cache (TTL: 3 minutes)
    if (useCache) {
      apiCache.set(cacheKey, data, 3 * 60 * 1000);
    }
    
    return data;
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/projects', data);
    const result = response.data;
    
    // Invalider le cache des projets
    apiCache.invalidatePattern('projects:');
    
    return result;
  },
  
  update: async (projectId: string, data: any) => {
    const response = await apiClient.put(`/projects/${projectId}`, data);
    const result = response.data;
    
    // Invalider le cache
    apiCache.delete(`projects:${projectId}`);
    apiCache.invalidatePattern('projects:');
    
    return result;
  },
  
  delete: async (projectId: string) => {
    const response = await apiClient.delete(`/projects/${projectId}`);
    
    // Invalider le cache
    apiCache.delete(`projects:${projectId}`);
    apiCache.invalidatePattern('projects:');
    
    return response.data;
  },
};

// Builds API
export const buildsApi = {
  getAll: async (projectId: string | null = null) => {
    let url = '/builds';
    if (projectId) url += `?project_id=${projectId}`;
    const response = await apiClient.get(url);
    return response.data;
  },
  
  getOne: async (buildId: string) => {
    const response = await apiClient.get(`/builds/${buildId}`);
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/builds', data);
    return response.data;
  },
  
  download: async (buildId: string): Promise<Blob> => {
    try {
      const response = await apiClient.get(`/builds/${buildId}/download`, {
        responseType: 'blob', // TRÈS IMPORTANT pour recevoir un blob
        timeout: 60000 // 60 secondes pour les gros fichiers
      });
      
      // Vérifier que la réponse est bien un blob
      if (!(response.data instanceof Blob)) {
        throw new Error('Réponse invalide: le serveur n\'a pas retourné un fichier');
      }
      
      return response.data;
    } catch (error: any) {
      // Si l'erreur est un blob (erreur JSON dans un blob), essayer de la parser
      if (error.response?.data instanceof Blob) {
        const text = await error.response.data.text();
        try {
          const errorData = JSON.parse(text);
          throw new Error(errorData.detail || 'Erreur lors du téléchargement');
        } catch {
          throw new Error('Erreur lors du téléchargement');
        }
      }
      throw error;
    }
  },
  
  /**
   * Télécharge un build avec indicateur de progression
   * Utilise fetch directement pour le streaming avec progression
   */
  downloadWithProgress: async (
    buildId: string,
    onProgress?: (progress: number, loaded: number, total: number) => void
  ): Promise<{ blob: Blob; filename: string }> => {
    try {
      logger.info(`📥 Démarrage du téléchargement avec progression du build ${buildId}...`);
      
      // Récupérer le token depuis la session
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;
      
      if (!token) {
        throw new Error('Vous devez être connecté pour télécharger');
      }
      
      // Utiliser fetch pour le streaming avec progression
      const BACKEND_URL = process.env.NODE_ENV === 'production' 
        ? (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000')
        : 'http://localhost:8000';
      
      const response = await fetch(`${BACKEND_URL}/api/builds/${buildId}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ 
          detail: `HTTP ${response.status}: ${response.statusText}` 
        }));
        throw new Error(error.detail || 'Échec du téléchargement');
      }
      
      // Récupérer la taille totale
      const contentLength = response.headers.get('Content-Length');
      const total = contentLength ? parseInt(contentLength, 10) : 0;
      
      logger.info(`📊 Taille totale: ${(total / 1024 / 1024).toFixed(2)} MB`);
      
      const reader = response.body?.getReader();
      if (!reader) throw new Error('Streaming non supporté');
      
      const chunks: Uint8Array[] = [];
      let receivedLength = 0;
      
      // Lire le stream chunk par chunk
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        chunks.push(value);
        receivedLength += value.length;
        
        // Notifier la progression
        if (onProgress && total > 0) {
          const progress = (receivedLength / total) * 100;
          onProgress(progress, receivedLength, total);
        }
      }
      
      logger.info('✅ Téléchargement terminé, assemblage du fichier...');
      
      // Combiner tous les chunks en un seul blob
      const blob = new Blob(chunks as BlobPart[]);
      
      // Extraire le nom du fichier depuis les headers
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `build-${buildId}.apk`;
      
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, '');
        }
      }
      
      return { blob, filename };
    } catch (error) {
      logger.error('❌ Erreur de téléchargement avec progression:', error);
      throw error;
    }
  },
  
  delete: async (buildId: string) => {
    const response = await apiClient.delete(`/builds/${buildId}`);
    // Invalider le cache des builds si nécessaire
    return response.data;
  },
  
  deleteAll: async () => {
    const response = await apiClient.delete('/builds');
    // Invalider le cache des builds si nécessaire
    return response.data;
  },
};

// API Keys
export const apiKeysApi = {
  getAll: async () => {
    const response = await apiClient.get('/api-keys');
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/api-keys', data);
    return response.data;
  },
  
  delete: async (keyId: string) => {
    const response = await apiClient.delete(`/api-keys/${keyId}`);
    return response.data;
  },
};

// Stats API
export const statsApi = {
  get: async () => {
    const response = await apiClient.get('/stats');
    return response.data;
  },
};

// Features API
export const featuresApi = {
  getAll: async () => {
    const response = await apiClient.get('/features');
    return response.data;
  },
};

// Admin API
export const adminApi = {
  getUsers: async (page: number = 1, limit: number = 20, includeAuthOnly: boolean = true) => {
    const response = await apiClient.get(`/admin/users?page=${page}&limit=${limit}&include_auth_only=${includeAuthOnly}`);
    return response.data;
  },
  
  createUser: async (data: { email: string; password: string; name: string; role?: string }) => {
    const response = await apiClient.post('/admin/users', data);
    return response.data;
  },
  
  updateUser: async (userId: string, data: any) => {
    const response = await apiClient.put(`/admin/users/${userId}`, data);
    return response.data;
  },
  
  deleteUser: async (userId: string) => {
    const response = await apiClient.delete(`/admin/users/${userId}`);
    return response.data;
  },
  
  getProjects: async (page: number = 1, limit: number = 20) => {
    const response = await apiClient.get(`/admin/projects?page=${page}&limit=${limit}`);
    return response.data;
  },
  
  deleteProject: async (projectId: string) => {
    const response = await apiClient.delete(`/admin/projects/${projectId}`);
    return response.data;
  },
  
  getBuilds: async (page: number = 1, limit: number = 20, status?: string) => {
    let url = `/admin/builds?page=${page}&limit=${limit}`;
    if (status) url += `&status=${status}`;
    const response = await apiClient.get(url);
    return response.data;
  },
  
  getLogs: async (page: number = 1, limit: number = 50, level?: string, category?: string) => {
    let url = `/admin/logs?page=${page}&limit=${limit}`;
    if (level) url += `&level=${level}`;
    if (category) url += `&category=${category}`;
    const response = await apiClient.get(url);
    return response.data;
  },
  
  getAnalytics: async () => {
    const response = await apiClient.get('/admin/analytics');
    return response.data;
  },
  
  getConfig: async () => {
    const response = await apiClient.get('/admin/config');
    return response.data;
  },
  
  updateConfig: async (config: any) => {
    const response = await apiClient.put('/admin/config', config);
    return response.data;
  },
  
  syncUser: async (userId: string) => {
    const response = await apiClient.post(`/admin/users/sync/${userId}`);
    return response.data;
  },
  
  getTemplates: async () => {
    const response = await apiClient.get('/admin/templates');
    return response.data;
  },
  
  getTemplate: async (templateId: string) => {
    const response = await apiClient.get(`/admin/templates/${templateId}`);
    return response.data;
  },
  
  createTemplate: async (data: any) => {
    const response = await apiClient.post('/admin/templates', data);
    return response.data;
  },
  
  updateTemplate: async (templateId: string, data: any) => {
    const response = await apiClient.put(`/admin/templates/${templateId}`, data);
    return response.data;
  },
  
  deleteTemplate: async (templateId: string) => {
    const response = await apiClient.delete(`/admin/templates/${templateId}`);
    return response.data;
  },
  
  getVisitStats: async () => {
    const response = await apiClient.get('/admin/visit-stats');
    return response.data;
  },
};

export default {
  projects: projectsApi,
  builds: buildsApi,
  apiKeys: apiKeysApi,
  stats: statsApi,
  features: featuresApi,
  admin: adminApi,
};
