import axios from 'axios';
import { createClient } from './supabase';

const API_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000') + '/api';

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
        console.error('[API] Error getting session:', sessionError);
        // Ne pas bloquer la requête, continuer sans token
        return config;
      }
      
      if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
      } else {
        console.warn('[API] No access token found in session');
      }
    } catch (error) {
      console.error('[API] Failed to get session in interceptor:', error);
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
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      console.warn(`[API] Backend non disponible sur ${backendUrl}`);
      
      const customError = new Error('Le serveur backend n\'est pas disponible. Veuillez démarrer le serveur avec: npm run dev');
      (customError as any).isConnectionError = true;
      (customError as any).backendUrl = backendUrl;
      return Promise.reject(customError);
    }
    
    // Gérer les erreurs 401 (Unauthorized) - NE PAS déconnecter automatiquement
    if (error.response?.status === 401) {
      console.warn('[API] Unauthorized request (401):', {
        url: error.config?.url,
        message: error.response?.data?.detail || 'Unauthorized'
      });
      
      // Ne pas déconnecter automatiquement, juste logger l'erreur
      // L'application décidera si une déconnexion est nécessaire
    }
    
    // Gérer les erreurs 403 (Forbidden)
    if (error.response?.status === 403) {
      console.warn('[API] Forbidden request (403):', {
        url: error.config?.url,
        message: error.response?.data?.detail || 'Forbidden'
      });
    }
    
    return Promise.reject(error);
  }
);

// Projects API
export const projectsApi = {
  getAll: async () => {
    const response = await apiClient.get('/projects');
    return response.data;
  },
  
  getOne: async (projectId: string) => {
    const response = await apiClient.get(`/projects/${projectId}`);
    return response.data;
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/projects', data);
    return response.data;
  },
  
  update: async (projectId: string, data: any) => {
    const response = await apiClient.put(`/projects/${projectId}`, data);
    return response.data;
  },
  
  delete: async (projectId: string) => {
    const response = await apiClient.delete(`/projects/${projectId}`);
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
