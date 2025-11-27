/**
 * API {��I
 */

// ==================== (7�s ====================
export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  role: 'admin' | 'user' | 'guest'
  is_active: boolean
  created_at: string
  last_login: string | null
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

// ==================== �c�s ====================
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

// ==================== "�s ====================
export interface SearchRequest {
  query: string
  top_k?: number
}

export interface SearchResult {
  chunk_id: number
  document_id: number
  text: string
  score: number
}

export interface SearchResponse {
  query: string
  results: SearchResult[]
  count: number
}

// ==================== �T�s ====================
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

// ==================== (͔ ====================
export interface ApiError {
  error: string
  detail?: string
}

export interface HealthResponse {
  status: string
}
