/**
 * API Client
 */
import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  SearchRequest,
  SearchResponse,
  UploadResponse,
  QARequest,
  QAResponse,
  HealthResponse,
} from './types'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - automatically add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ==================== Auth API ====================
export const authApi = {
  // Login
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/api/auth/login', data)
    const payload = response.data as AuthResponse & { error?: string }

    if (!payload.access_token) {
      throw new Error(payload.error || 'Login failed')
    }

    // Save token
    localStorage.setItem('access_token', payload.access_token)
    return payload
  },

  // Register
  register: async (data: RegisterRequest): Promise<{ message: string; user_id: number }> => {
    const response = await api.post('/api/auth/register', data)
    return response.data
  },

  // Get current user info
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/api/auth/me')
    return response.data
  },

  // Logout
  logout: () => {
    localStorage.removeItem('access_token')
    window.location.href = '/login'
  },

  // Check if user is authenticated
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('access_token')
  },
}

// ==================== Document API ====================
export const documentApi = {
  // Upload document
  upload: async (
    file: File,
    onProgress?: (progress: number) => void,
    folderId?: number | null
  ): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    if (folderId !== undefined && folderId !== null) {
      formData.append('folder_id', folderId.toString())
    }

    const response = await api.post<UploadResponse>('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
    return response.data
  },

  // Get document list with pagination
  list: async (params?: {
    page?: number
    page_size?: number
    status?: string
    file_type?: string
    folder_id?: number | null
    search?: string
  }): Promise<{
    documents: any[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }> => {
    const response = await api.get('/api/documents', { params })
    return response.data
  },

  // Get document details by ID
  getById: async (id: number): Promise<any> => {
    const response = await api.get(`/api/documents/${id}`)
    return response.data
  },

  // Delete document
  delete: async (id: number): Promise<{ message: string; document_id: number }> => {
    const response = await api.delete(`/api/documents/${id}`)
    return response.data
  },

  // Download document
  download: async (id: number): Promise<Blob> => {
    const response = await api.get(`/api/documents/${id}/download`, { responseType: 'blob' })
    return response.data
  },

  // Get document statistics
  getStats: async (): Promise<{
    total_documents: number
    total_storage_bytes: number
    by_status: Record<string, number>
    by_type: Record<string, number>
  }> => {
    const response = await api.get('/api/documents/stats/summary')
    return response.data
  },
}

// ==================== Search API ====================
export const searchApi = {
  // Search documents
  search: async (data: SearchRequest): Promise<SearchResponse> => {
    const response = await api.post<SearchResponse>('/api/search', data)
    return response.data
  },
}

// ==================== QA API ====================
export const qaApi = {
  // Ask question with longer timeout for LLM processing
  ask: async (data: QARequest): Promise<QAResponse> => {
    // QA requests need longer timeout because LLM may take up to 60s
    const response = await api.post<QAResponse>('/api/qa', data, {
      timeout: 90000, // 90 seconds - longer than backend LLM timeout (60s)
    })
    return response.data
  },
}

// ==================== Folder API ====================
export const folderApi = {
  // List folders
  list: async (parentId?: number | null): Promise<any[]> => {
    const params = parentId !== undefined ? { parent_id: parentId } : {}
    const response = await api.get('/api/folders', { params })
    return response.data
  },

  // Get folder tree
  getTree: async (): Promise<any[]> => {
    const response = await api.get('/api/folders/tree')
    return response.data
  },

  // Create folder
  create: async (data: {
    name: string
    description?: string
    parent_id?: number | null
  }): Promise<any> => {
    const response = await api.post('/api/folders', data)
    return response.data
  },

  // Update folder
  update: async (
    id: number,
    data: {
      name?: string
      description?: string
      parent_id?: number | null
    }
  ): Promise<any> => {
    const response = await api.put(`/api/folders/${id}`, data)
    return response.data
  },

  // Delete folder
  delete: async (id: number): Promise<{ message: string; folder_id: number }> => {
    const response = await api.delete(`/api/folders/${id}`)
    return response.data
  },
}

// ==================== System API ====================
export const systemApi = {
  // Health check
  health: async (): Promise<HealthResponse> => {
    const response = await api.get<HealthResponse>('/health')
    return response.data
  },
}

export default api
