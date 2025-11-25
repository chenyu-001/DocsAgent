import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { documentApi } from '../api/client'
import {
  FileText,
  ArrowLeft,
  Loader,
  AlertCircle,
  Calendar,
  User,
  Hash,
  FileType,
  HardDrive
} from 'lucide-react'
import { DocumentStatusBadge } from '../components/DocumentStatusBadge'
import type { Document as DocumentType } from '../api/types'

interface DocumentDetail extends DocumentType {
  chunks: Array<{
    id: number
    text: string
    chunk_index: number
  }>
}

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [document, setDocument] = useState<DocumentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    if (id) {
      fetchDocument(parseInt(id))
    }
  }, [id])

  const fetchDocument = async (docId: number) => {
    try {
      setLoading(true)
      const response = await documentApi.getById(docId)
      setDocument(response)
      setError(null)
    } catch (err: any) {
      console.error('Failed to fetch document:', err)
      setError(err.response?.data?.detail || 'Failed to load document')
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const filteredChunks = document?.chunks?.filter(chunk =>
    chunk.text.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading document...</p>
        </div>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-900 font-medium mb-2">Failed to load document</p>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate('/documents')}
            className="text-blue-600 hover:text-blue-700"
          >
            Back to documents
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center space-x-2 text-gray-700 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back</span>
            </button>
            <DocumentStatusBadge status={document.status} />
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Document Info Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-start gap-4">
            <FileText className="w-12 h-12 text-blue-600 flex-shrink-0" />
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {document.title || document.filename}
              </h1>
              {document.title && (
                <p className="text-sm text-gray-500 mb-3">{document.filename}</p>
              )}

              {/* Metadata Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <div className="flex items-center gap-2 text-sm">
                  <FileType className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-gray-500">Type</div>
                    <div className="font-medium">{document.file_type}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <HardDrive className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-gray-500">Size</div>
                    <div className="font-medium">{formatFileSize(document.file_size)}</div>
                  </div>
                </div>
                {document.page_count && (
                  <div className="flex items-center gap-2 text-sm">
                    <Hash className="w-4 h-4 text-gray-400" />
                    <div>
                      <div className="text-gray-500">Pages</div>
                      <div className="font-medium">{document.page_count}</div>
                    </div>
                  </div>
                )}
                {document.word_count && (
                  <div className="flex items-center gap-2 text-sm">
                    <Hash className="w-4 h-4 text-gray-400" />
                    <div>
                      <div className="text-gray-500">Words</div>
                      <div className="font-medium">{document.word_count.toLocaleString()}</div>
                    </div>
                  </div>
                )}
                {document.author && (
                  <div className="flex items-center gap-2 text-sm">
                    <User className="w-4 h-4 text-gray-400" />
                    <div>
                      <div className="text-gray-500">Author</div>
                      <div className="font-medium">{document.author}</div>
                    </div>
                  </div>
                )}
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-gray-500">Uploaded</div>
                    <div className="font-medium text-xs">{formatDate(document.created_at)}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Content Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Document Content ({document.chunks?.length || 0} chunks)
            </h2>
            <div className="w-64">
              <input
                type="text"
                placeholder="Search in document..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {document.chunks && document.chunks.length > 0 ? (
            <div className="space-y-4">
              {filteredChunks.map((chunk, index) => (
                <div
                  key={chunk.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-gray-500">
                      Chunk #{chunk.chunk_index + 1}
                    </span>
                    <span className="text-xs text-gray-400">ID: {chunk.id}</span>
                  </div>
                  <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {chunk.text}
                  </div>
                </div>
              ))}

              {filteredChunks.length === 0 && searchTerm && (
                <div className="text-center py-8 text-gray-500">
                  No chunks found matching "{searchTerm}"
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No content available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
