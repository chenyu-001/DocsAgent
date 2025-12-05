/**
 * API 类型定义
 */

// ==================== 用户 ====================
export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  role: 'admin' | 'user' | 'guest'
  is_active: boolean
  created_at: string
  last_login: string | null
  // Platform admin fields
  platform_role?: 'super_admin' | 'ops' | 'support' | 'auditor' | null
  is_platform_admin?: boolean
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

// ==================== 文档 ====================
export interface Document {
  id: number
  filename: string
  file_hash: string
  file_type: 'PDF' | 'DOCX' | 'PPTX' | 'XLSX' | 'TXT' | 'MD' | 'HTML' | 'OTHER'
  file_size: number
  title: string | null
  author: string | null
  subject: string | null
  keywords: string | null
  page_count: number | null
  word_count: number | null
  status: 'UPLOADING' | 'PARSING' | 'EMBEDDING' | 'READY' | 'FAILED'
  owner_id: number
  folder_id: number | null
  folder_path: string
  folder_name: string
  created_at: string
  updated_at: string
  parsed_at: string | null
}

export interface UploadResponse {
  message: string
  document_id: number
  filename: string
  chunks: number
}

// ==================== 搜索 ====================
export interface SearchRequest {
  query: string
  top_k?: number
}

export interface SearchResult {
  chunk_id: number
  document_id: number
  text: string
  score: number
  filename?: string
  folder_path?: string
  title?: string
}

export interface SearchResponse {
  query: string
  results: SearchResult[]
  count: number
}

// ==================== 问答 ====================
export interface QARequest {
  question: string
  top_k?: number
}

export interface QAResponse {
  question: string
  answer: string
  sources: SearchResult[]
  retrieval_time: number
  llm_time: number
  total_time: number
}

// ==================== 租户管理 ====================
export interface Tenant {
  id: string
  name: string
  slug: string
  description: string | null
  deploy_mode: 'CLOUD' | 'HYBRID' | 'LOCAL'
  status: 'ACTIVE' | 'SUSPENDED' | 'ARCHIVED' | 'TRIAL'
  storage_quota_bytes: number
  storage_used_bytes: number
  storage_usage_percent: number
  user_quota: number
  user_count: number
  document_quota: number
  document_count: number
  created_at: string
}

export interface TenantRole {
  id: string
  tenant_id: string
  name: string
  display_name: string
  description: string | null
  level: number
  permissions: number
  permissions_string: string
  is_system: boolean
  is_default: boolean
}

export interface TenantUser {
  id: string
  tenant_id: string
  user_id: number
  role_id: string | null
  role_name: string | null
  department_id: string | null
  department_name: string | null
  status: string
  joined_at: string
}

// ==================== 错误 ====================
export interface ApiError {
  error: string
  detail?: string
}

export interface HealthResponse {
  status: string
}
