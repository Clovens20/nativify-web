import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL + '/api';

// Projects API
export const projectsApi = {
  getAll: async (userId: string) => {
    const response = await axios.get(`${API_URL}/projects?user_id=${userId}`);
    return response.data;
  },
  
  getOne: async (projectId: string, userId: string) => {
    const response = await axios.get(`${API_URL}/projects/${projectId}?user_id=${userId}`);
    return response.data;
  },
  
  create: async (data: any, userId: string) => {
    const response = await axios.post(`${API_URL}/projects?user_id=${userId}`, data);
    return response.data;
  },
  
  update: async (projectId: string, data: any, userId: string) => {
    const response = await axios.put(`${API_URL}/projects/${projectId}?user_id=${userId}`, data);
    return response.data;
  },
  
  delete: async (projectId: string, userId: string) => {
    const response = await axios.delete(`${API_URL}/projects/${projectId}?user_id=${userId}`);
    return response.data;
  },
};

// Builds API
export const buildsApi = {
  getAll: async (userId: string, projectId: string | null = null) => {
    let url = `${API_URL}/builds?user_id=${userId}`;
    if (projectId) url += `&project_id=${projectId}`;
    const response = await axios.get(url);
    return response.data;
  },
  
  getOne: async (buildId: string, userId: string) => {
    const response = await axios.get(`${API_URL}/builds/${buildId}?user_id=${userId}`);
    return response.data;
  },
  
  create: async (data: any, userId: string) => {
    const response = await axios.post(`${API_URL}/builds?user_id=${userId}`, data);
    return response.data;
  },
  
  download: (buildId: string, userId: string) => {
    return `${API_URL}/builds/${buildId}/download?user_id=${userId}`;
  },
};

// API Keys
export const apiKeysApi = {
  getAll: async (userId: string) => {
    const response = await axios.get(`${API_URL}/api-keys?user_id=${userId}`);
    return response.data;
  },
  
  create: async (data: any, userId: string) => {
    const response = await axios.post(`${API_URL}/api-keys?user_id=${userId}`, data);
    return response.data;
  },
  
  delete: async (keyId: string, userId: string) => {
    const response = await axios.delete(`${API_URL}/api-keys/${keyId}?user_id=${userId}`);
    return response.data;
  },
};

// Stats API
export const statsApi = {
  get: async (userId: string) => {
    const response = await axios.get(`${API_URL}/stats?user_id=${userId}`);
    return response.data;
  },
};

// Features API
export const featuresApi = {
  getAll: async () => {
    const response = await axios.get(`${API_URL}/features`);
    return response.data;
  },
};

// Admin API
export const adminApi = {
  getUsers: async (adminId: string, page: number = 1, limit: number = 20) => {
    const response = await axios.get(`${API_URL}/admin/users?admin_id=${adminId}&page=${page}&limit=${limit}`);
    return response.data;
  },
  
  updateUser: async (userId: string, adminId: string, data: any) => {
    const response = await axios.put(`${API_URL}/admin/users/${userId}?admin_id=${adminId}`, data);
    return response.data;
  },
  
  getBuilds: async (adminId: string, page: number = 1, limit: number = 20, status?: string) => {
    let url = `${API_URL}/admin/builds?admin_id=${adminId}&page=${page}&limit=${limit}`;
    if (status) url += `&status=${status}`;
    const response = await axios.get(url);
    return response.data;
  },
  
  getLogs: async (adminId: string, page: number = 1, limit: number = 50, level?: string, category?: string) => {
    let url = `${API_URL}/admin/logs?admin_id=${adminId}&page=${page}&limit=${limit}`;
    if (level) url += `&level=${level}`;
    if (category) url += `&category=${category}`;
    const response = await axios.get(url);
    return response.data;
  },
  
  getAnalytics: async (adminId: string) => {
    const response = await axios.get(`${API_URL}/admin/analytics?admin_id=${adminId}`);
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
