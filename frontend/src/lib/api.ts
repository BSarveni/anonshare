import axios from 'axios'

export const apiBaseUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? ''

if (!apiBaseUrl && import.meta.env.PROD) {
  console.error(
    'VITE_API_URL is missing. Set it in Railway frontend variables and redeploy.',
  )
}

export function apiRegisterUrl(): string {
  return apiBaseUrl ? `${apiBaseUrl}/api/auth/register` : '(VITE_API_URL not set — redeploy frontend)'
}

const api = axios.create({
  baseURL: apiBaseUrl || undefined,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export default api

export type User = {
  id: string
  pseudonym: string
  is_admin: boolean
  created_at: string
}

export type Post = {
  id: string
  image_url: string
  caption: string | null
  is_flagged: boolean
  created_at: string
  poster_pseudonym: string
}

export type Group = {
  id: string
  name: string
  created_at: string
}

export type ChatMessage = {
  id?: string
  group_id?: string
  content: string
  pseudonym: string
  created_at: string
  type?: string
}

export type FlaggedEvent = {
  id: string
  user_id: string
  user_pseudonym: string
  event_type: string
  detail: string
  resolved: boolean
  created_at: string
}

export const authApi = {
  register: (password: string) =>
    api.post<{ pseudonym: string; access_token: string }>('/api/auth/register', { password }),
  login: (pseudonym: string, password: string) =>
    api.post<{ access_token: string }>('/api/auth/login', { pseudonym, password }),
  me: () => api.get<User>('/api/auth/me'),
}

export const postsApi = {
  feed: (skip: number, limit: number) =>
    api.get<Post[]>('/api/posts/feed', { params: { skip, limit } }),
  upload: (image_url: string, caption?: string) =>
    api.post<Post>('/api/posts/upload', { image_url, caption: caption || null }),
}

export const groupsApi = {
  list: () => api.get<Group[]>('/api/groups/'),
  create: (name: string) => api.post<Group>('/api/groups/create', { name }),
  messages: (groupId: string) => api.get<ChatMessage[]>(`/api/groups/${groupId}/messages`),
  sendMessage: (groupId: string, content: string) =>
    api.post<ChatMessage>(`/api/groups/${groupId}/message`, { content }),
}

export const adminApi = {
  flags: () => api.get<FlaggedEvent[]>('/api/admin/flags'),
  ban: (userId: string) => api.post(`/api/admin/ban/${userId}`),
  resolve: (flagId: string) => api.post(`/api/admin/resolve/${flagId}`),
}
