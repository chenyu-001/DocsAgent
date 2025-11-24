import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { documentApi, folderApi } from '../api/client'
import FolderTree from '../components/FolderTree'
import { FileText, Trash2, Eye, Download, Loader, ChevronLeft, ChevronRight } from 'lucide-react'

interface Document {
  id: number
  filename: string
  file_type: string
  file_size: number
  status: string
  created_at: string
  page_count: number | null
  word_count: number | null
}

export default function DocumentsListPage() {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [filterType, setFilterType] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [stats, setStats] = useState<any>(null)

  // Folder state
  const [folders, setFolders] = useState<any[]>([])
  const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null)

  const pageSize = 10

  useEffect(() => {
    fetchDocuments()
    fetchStats()
    fetchFolders()
  }, [page, filterType, filterStatus, searchQuery, selectedFolderId])

  const fetchFolders = async () => {
    try {
      const response = await folderApi.getTree()
      setFolders(response)
    } catch (error) {
      console.error('Failed to fetch folders:', error)
    }
  }

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const params: any = {
        page,
        page_size: pageSize,
      }
      if (filterType) params.file_type = filterType
      if (filterStatus) params.status = filterStatus
      if (searchQuery) params.search = searchQuery
      if (selectedFolderId !== null) params.folder_id = selectedFolderId

      const response = await documentApi.list(params)
      setDocuments(response.documents)
      setTotal(response.total)
      setTotalPages(response.total_pages)
    } catch (error) {
      console.error('Failed to fetch documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await documentApi.getStats()
      setStats(response)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const handleDelete = async (id: number, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return

    try {
      await documentApi.delete(id)
      fetchDocuments()
      fetchStats()
    } catch (error) {
      console.error('Failed to delete document:', error)
      alert('Failed to delete document')
    }
  }

  const handleView = async (id: number) => {
    try {
      const token = localStorage.getItem('access_token')
      const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/documents/${id}/view`

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to view document')
      }

      const blob = await response.blob()
      const blobUrl = URL.createObjectURL(blob)
      window.open(blobUrl, '_blank')

      // Clean up blob URL after a delay
      setTimeout(() => URL.revokeObjectURL(blobUrl), 100)
    } catch (error) {
      console.error('Failed to view document:', error)
      alert('Failed to open document')
    }
  }

  const handleDownload = async (id: number, filename: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/documents/${id}/download`

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to download document')
      }

      const blob = await response.blob()
      const blobUrl = URL.createObjectURL(blob)

      // Create a temporary link and click it to trigger download
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      // Clean up blob URL
      URL.revokeObjectURL(blobUrl)
    } catch (error) {
      console.error('Failed to download document:', error)
      alert('Failed to download document')
    }
  }

  const handleCreateFolder = async (parentId: number | null) => {
    const folderName = prompt('Enter folder name:')
    if (!folderName) return

    try {
      await folderApi.create({
        name: folderName,
        parent_id: parentId,
      })
      fetchFolders()
    } catch (error: any) {
      console.error('Failed to create folder:', error)
      alert(error.response?.data?.detail || 'Failed to create folder')
    }
  }

  const handleDeleteFolder = async (folderId: number, folderName: string) => {
    if (!confirm(`Are you sure you want to delete folder "${folderName}"? This will also delete all documents in this folder.`)) return

    try {
      await folderApi.delete(folderId)
      fetchFolders()
      fetchDocuments()
      if (selectedFolderId === folderId) {
        setSelectedFolderId(null)
      }
    } catch (error: any) {
      console.error('Failed to delete folder:', error)
      alert(error.response?.data?.detail || 'Failed to delete folder')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      READY: 'bg-green-100 text-green-800',
      PARSING: 'bg-blue-100 text-blue-800',
      EMBEDDING: 'bg-yellow-100 text-yellow-800',
      FAILED: 'bg-red-100 text-red-800',
      UPLOADING: 'bg-gray-100 text-gray-800',
    }
    const labels: Record<string, string> = {
      READY: 'Ready',
      PARSING: 'Parsing',
      EMBEDDING: 'Embedding',
      FAILED: 'Failed',
      UPLOADING: 'Uploading',
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
        {labels[status] || status}
      </span>
    )
  }

  const getFileIcon = (fileType: string) => {
    const color = {
      PDF: 'text-red-500',
      DOCX: 'text-blue-500',
      PPTX: 'text-orange-500',
      XLSX: 'text-green-500',
      TXT: 'text-gray-500',
      MD: 'text-purple-500',
    }[fileType] || 'text-gray-500'

    return <FileText className={`w-5 h-5 ${color}`} />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/search')}
                className="text-gray-600 hover:text-gray-900"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
              <h1 className="text-2xl font-bold text-gray-900">My Documents</h1>
            </div>
            <button
              onClick={() => navigate('/upload')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Upload New
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Total Documents</div>
              <div className="text-2xl font-bold text-gray-900">{stats.total_documents}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Storage Used</div>
              <div className="text-2xl font-bold text-gray-900">{formatFileSize(stats.total_storage_bytes)}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Ready</div>
              <div className="text-2xl font-bold text-green-600">{stats.by_status?.READY || 0}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Processing</div>
              <div className="text-2xl font-bold text-blue-600">
                {(stats.by_status?.PARSING || 0) + (stats.by_status?.EMBEDDING || 0)}
              </div>
            </div>
          </div>
        )}

        {/* Main Content - Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Folder Sidebar */}
          <div className="lg:col-span-1">
            <FolderTree
              folders={folders}
              selectedFolderId={selectedFolderId}
              onSelectFolder={(folderId) => {
                setSelectedFolderId(folderId)
                setPage(1)
              }}
              onCreateFolder={handleCreateFolder}
              onDeleteFolder={handleDeleteFolder}
            />
          </div>

          {/* Documents List */}
          <div className="lg:col-span-3">
            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-4 mb-6">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Search documents..."
                    value={searchQuery}
                    onChange={(e) => { setSearchQuery(e.target.value); setPage(1) }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <select
                  value={filterType}
                  onChange={(e) => { setFilterType(e.target.value); setPage(1) }}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Types</option>
                  <option value="PDF">PDF</option>
                  <option value="DOCX">Word</option>
                  <option value="PPTX">PowerPoint</option>
                  <option value="XLSX">Excel</option>
                  <option value="TXT">Text</option>
                  <option value="MD">Markdown</option>
                </select>
                <select
                  value={filterStatus}
                  onChange={(e) => { setFilterStatus(e.target.value); setPage(1) }}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Status</option>
                  <option value="READY">Ready</option>
                  <option value="PARSING">Parsing</option>
                  <option value="EMBEDDING">Embedding</option>
                  <option value="FAILED">Failed</option>
                </select>
              </div>
            </div>

            {/* Documents Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader className="w-8 h-8 animate-spin text-blue-600" />
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No documents found</p>
                  <button
                    onClick={() => navigate('/upload')}
                    className="mt-4 text-blue-600 hover:text-blue-700"
                  >
                    Upload your first document
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Document
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Size
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Uploaded
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {documents.map((doc) => (
                        <tr key={doc.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {getFileIcon(doc.file_type)}
                              <button
                                onClick={() => navigate(`/document/${doc.id}`)}
                                className="ml-2 text-sm font-medium text-gray-900 hover:text-blue-600"
                              >
                                {doc.filename}
                              </button>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-500">{doc.file_type}</span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-500">{formatFileSize(doc.file_size)}</span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {getStatusBadge(doc.status)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-500">
                              {new Date(doc.created_at).toLocaleDateString()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleView(doc.id)}
                                className="text-blue-600 hover:text-blue-900"
                                title="Open in browser"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDownload(doc.id, doc.filename)}
                                className="text-green-600 hover:text-green-900"
                                title="Download"
                              >
                                <Download className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(doc.id, doc.filename)}
                                className="text-red-600 hover:text-red-900"
                                title="Delete"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Pagination */}
              {!loading && totalPages > 1 && (
                <div className="px-6 py-4 flex items-center justify-between border-t border-gray-200">
                  <div className="text-sm text-gray-700">
                    Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} documents
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-3 py-1 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <span className="px-3 py-1">
                      Page {page} of {totalPages}
                    </span>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-3 py-1 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
