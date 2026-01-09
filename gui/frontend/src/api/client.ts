import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const api = axios.create({
  baseURL: '/api',
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API functions
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string, name: string) =>
    api.post('/auth/register', { email, password, name }),
  me: () => api.get('/auth/me'),
}

export const plansApi = {
  list: (params?: { page?: number; limit?: number }) =>
    api.get('/plans', { params }),
  get: (id: string) => api.get(`/plans/${id}`),
  create: (data: { name: string; description?: string }) =>
    api.post('/plans', data),
  update: (id: string, data: any) => api.put(`/plans/${id}`, data),
  delete: (id: string) => api.delete(`/plans/${id}`),
}

export const primitivesApi = {
  list: () => api.get('/primitives'),
  get: (id: string) => api.get(`/primitives/${id}`),
  search: (q: string) => api.get('/primitives/search', { params: { q } }),
}

export const validationApi = {
  validate: (planJson: any) => api.post('/validate', { plan_json: planJson }),
}

export const compileApi = {
  compile: (planJson: any) => api.post('/compile', { plan_json: planJson }),
  preview: (planJson: any) => api.post('/compile/preview', { plan_json: planJson }),
}

export const githubApi = {
  analyze: (repoUrl: string, branch?: string) =>
    api.post('/analyze/github', { repo_url: repoUrl, branch }),
}
