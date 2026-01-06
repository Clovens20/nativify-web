import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const getToken = () => localStorage.getItem('token');

const getUserId = () => {
  const token = getToken();
  if (!token) return null;
  // For now, we'll get user from stored data
  const userData = localStorage.getItem('user');
  return userData ? JSON.parse(userData).id : null;
};

// Projects API
export const projectsApi = {
  getAll: async (userId) => {
    const response = await axios.get(`${API_URL}/projects?user_id=${userId}`);
    return response.data;
  },
  
  getOne: async (projectId, userId) => {
    const response = await axios.get(`${API_URL}/projects/${projectId}?user_id=${userId}`);
    return response.data;
  },
  
  create: async (data, userId) => {
    const response = await axios.post(`${API_URL}/projects?user_id=${userId}`, data);
    return response.data;
  },
  
  update: async (projectId, data, userId) => {
    const response = await axios.put(`${API_URL}/projects/${projectId}?user_id=${userId}`, data);
    return response.data;
  },
  
  delete: async (projectId, userId) => {
    const response = await axios.delete(`${API_URL}/projects/${projectId}?user_id=${userId}`);
    return response.data;
  },
};

// Builds API
export const buildsApi = {
  getAll: async (userId, projectId = null) => {
    let url = `${API_URL}/builds?user_id=${userId}`;
    if (projectId) url += `&project_id=${projectId}`;
    const response = await axios.get(url);
    return response.data;
  },
  
  getOne: async (buildId, userId) => {
    const response = await axios.get(`${API_URL}/builds/${buildId}?user_id=${userId}`);
    return response.data;
  },
  
  create: async (data, userId) => {
    const response = await axios.post(`${API_URL}/builds?user_id=${userId}`, data);
    return response.data;
  },
  
  download: (buildId, userId) => {
    return `${API_URL}/builds/${buildId}/download?user_id=${userId}`;
  },
};

// API Keys
export const apiKeysApi = {
  getAll: async (userId) => {
    const response = await axios.get(`${API_URL}/api-keys?user_id=${userId}`);
    return response.data;
  },
  
  create: async (data, userId) => {
    const response = await axios.post(`${API_URL}/api-keys?user_id=${userId}`, data);
    return response.data;
  },
  
  delete: async (keyId, userId) => {
    const response = await axios.delete(`${API_URL}/api-keys/${keyId}?user_id=${userId}`);
    return response.data;
  },
};

// Stats API
export const statsApi = {
  get: async (userId) => {
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

// Generator API
export const generatorApi = {
  getSdk: (projectId, userId) => {
    return `${API_URL}/generator/sdk/${projectId}?user_id=${userId}`;
  },
  
  getTemplate: async (projectId, platform, userId) => {
    const response = await axios.get(`${API_URL}/generator/template/${projectId}/${platform}?user_id=${userId}`);
    return response.data;
  },
};

export default {
  projects: projectsApi,
  builds: buildsApi,
  apiKeys: apiKeysApi,
  stats: statsApi,
  features: featuresApi,
  generator: generatorApi,
};
