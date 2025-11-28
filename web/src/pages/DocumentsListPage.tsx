import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { documentApi, folderApi } from '../api/client'
import FolderTree from '../components/FolderTree'
import { FileText, Trash2, Download, Loader, ChevronLeft, ChevronRight, FolderOpen } from 'lucide-react'
import { DocumentStatusBadge } from '../components/DocumentStatusBadge'
import ConfirmDialog from '../components/ConfirmDialog'
import Toast, { ToastType } from '../components/Toast'
import InputDialog from '../components/InputDialog'
import type { Document as DocumentType } from '../api/types'

export default function DocumentsListPage() {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState<DocumentType[]>([])
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

  // Move dialog state
  const [moveDialogOpen, setMoveDialogOpen] = useState(false)
  const [documentToMove, setDocumentToMove] = useState<DocumentType | null>(null)
  const [targetFolderId, setTargetFolderId] = useState<number | null>(null)

  // Confirmation dialogs
  const [deleteConfirm, setDeleteConfirm] = useState<{ isOpen: boolean; id: number | null; filename: string }>({
    isOpen: false,
    id: null,
    filename: '',
  })
  const [deleteFolderConfirm, setDeleteFolderConfirm] = useState<{
    isOpen: boolean
    id: number | null
    name: string
  }>({ isOpen: false, id: null, name: '' })

  // Input dialog
  const [createFolderDialog, setCreateFolderDialog] = useState<{
    isOpen: boolean
    parentId: number | null
  }>({ isOpen: false, parentId: null })

  // Toast notification
  const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null)

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

  const handleDelete = (id: number, filename: string) => {
    setDeleteConfirm({ isOpen: true, id, filename })
  }

  const confirmDelete = async () => {
    if (!deleteConfirm.id) return

    try {
      await documentApi.delete(deleteConfirm.id)
      setDeleteConfirm({ isOpen: false, id: null, filename: '' })
      fetchDocuments()
      fetchStats()
      setToast({ message: 'Document deleted successfully', type: 'success' })
    } catch (error) {
      console.error('Failed to delete document:', error)
      setToast({ message: 'Failed to delete document', type: 'error' })
    }
  }

  const handleMoveClick = (doc: DocumentType) => {
    setDocumentToMove(doc)
    setTargetFolderId(doc.folder_id)
    setMoveDialogOpen(true)
  }

  const handleMoveConfirm = async () => {
    if (!documentToMove) return

    try {
      await documentApi.move(documentToMove.id, targetFolderId)
      setMoveDialogOpen(false)
      setDocumentToMove(null)
      fetchDocuments()
      setToast({ message: 'Document moved successfully', type: 'success' })
    } catch (error) {
      console.error('Failed to move document:', error)
      setToast({ message: 'Failed to move document', type: 'error' })
    }
  }

  const flattenFolders = (folders: any[], level = 0): any[] => {
    const result: any[] = []
    folders.forEach((folder) => {
      result.push({ ...folder, level })
      if (folder.children && folder.children.length > 0) {
        result.push(...flattenFolders(folder.children, level + 1))
      }
    })
    return result
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
        // Try to get error details from response
        let errorMessage = 'Failed to download document'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorMessage
        } catch {
          errorMessage = `Failed to download document (${response.status})`
        }
        throw new Error(errorMessage)
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
      setToast({ message: 'Document downloaded successfully', type: 'success' })
    } catch (error: any) {
      console.error('Failed to download document:', error)
      setToast({ message: error.message || 'Failed to download document', type: 'error' })
    }
  }

  const handleCreateFolder = (parentId: number | null) => {
    setCreateFolderDialog({ isOpen: true, parentId })
  }

  const confirmCreateFolder = async (folderName: string) => {
    try {
      await folderApi.create({
        name: folderName,
        parent_id: createFolderDialog.parentId,
      })
      setCreateFolderDialog({ isOpen: false, parentId: null })
      fetchFolders()
      setToast({ message: 'Folder created successfully', type: 'success' })
    } catch (error: any) {
      console.error('Failed to create folder:', error)
      setToast({ message: error.response?.data?.detail || 'Failed to create folder', type: 'error' })
    }
  }

  const handleDeleteFolder = (folderId: number, folderName: string) => {
    setDeleteFolderConfirm({ isOpen: true, id: folderId, name: folderName })
  }

  const confirmDeleteFolder = async () => {
    if (!deleteFolderConfirm.id) return

    try {
      await folderApi.delete(deleteFolderConfirm.id)
      setDeleteFolderConfirm({ isOpen: false, id: null, name: '' })
      fetchFolders()
      fetchDocuments()
      if (selectedFolderId === deleteFolderConfirm.id) {
        setSelectedFolderId(null)
      }
      setToast({ message: 'Folder deleted successfully', type: 'success' })
    } catch (error: any) {
      console.error('Failed to delete folder:', error)
      setToast({ message: error.response?.data?.detail || 'Failed to delete folder', type: 'error' })
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const getFileIcon = (fileType: DocumentType['file_type']) => {
    const color = {
      PDF: 'text-red-500',
      DOCX: 'text-blue-500',
      PPTX: 'text-orange-500',
      XLSX: 'text-green-500',
      TXT: 'text-gray-500',
      MD: 'text-purple-500',
      HTML: 'text-pink-500',
      OTHER: 'text-gray-500',
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
              onClick={() => navigate('/upload', { state: { folderId: selectedFolderId } })}
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
              <div className="text-2xl font-bold text-green-600">{stats.by_status?.ready || 0}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Processing</div>
              <div className="text-2xl font-bold text-blue-600">
                {(stats.by_status?.parsing || 0) + (stats.by_status?.embedding || 0)}
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
                    onClick={() => navigate('/upload', { state: { folderId: selectedFolderId } })}
                    className="mt-4 text-blue-600 hover:text-blue-700"
                  >
                    Upload your first document
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full table-fixed">
                    <colgroup>
                      <col className="w-[35%]" />
                      <col className="w-[15%]" />
                      <col className="w-[8%]" />
                      <col className="w-[10%]" />
                      <col className="w-[10%]" />
                      <col className="w-[12%]" />
                      <col className="w-[10%]" />
                    </colgroup>
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Document
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Path
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Size
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Uploaded
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {documents.map((doc) => (
                        <tr key={doc.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <div className="flex items-center min-w-0">
                              <div className="flex-shrink-0">
                                {getFileIcon(doc.file_type)}
                              </div>
                              <button
                                onClick={() => navigate(`/document/${doc.id}`)}
                                className="ml-2 text-sm font-medium text-gray-900 hover:text-blue-600 truncate"
                                title={doc.filename}
                              >
                                {doc.filename}
                              </button>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-gray-600 truncate block" title={doc.folder_path || '/'}>
                              {doc.folder_path || '/'}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-gray-600">{doc.file_type}</span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-gray-600">{formatFileSize(doc.file_size)}</span>
                          </td>
                          <td className="px-4 py-3">
                            <DocumentStatusBadge status={doc.status} />
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-gray-600">
                              {new Date(doc.created_at).toLocaleDateString()}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleDownload(doc.id, doc.filename)}
                                className="text-blue-600 hover:text-blue-900 transition-colors"
                                title="Download"
                              >
                                <Download className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleMoveClick(doc)}
                                className="text-orange-600 hover:text-orange-900 transition-colors"
                                title="Move to folder"
                              >
                                <FolderOpen className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(doc.id, doc.filename)}
                                className="text-red-600 hover:text-red-900 transition-colors"
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

      {/* Move Document Dialog */}
      {moveDialogOpen && documentToMove && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 animate-fadeIn">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Move Document
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Move "{documentToMove.filename}" to:
            </p>
            <select
              value={targetFolderId ?? ''}
              onChange={(e) => setTargetFolderId(e.target.value === '' ? null : Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-6"
            >
              <option value="">Root / No Folder</option>
              {flattenFolders(folders).map((folder) => (
                <option key={folder.id} value={folder.id}>
                  {'  '.repeat(folder.level)}📁 {folder.name}
                </option>
              ))}
            </select>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setMoveDialogOpen(false)
                  setDocumentToMove(null)
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleMoveConfirm}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Move
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Document Confirmation */}
      <ConfirmDialog
        isOpen={deleteConfirm.isOpen}
        title="Delete Document"
        message={`Are you sure you want to delete "${deleteConfirm.filename}"?\n\nThis action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        type="danger"
        onConfirm={confirmDelete}
        onCancel={() => setDeleteConfirm({ isOpen: false, id: null, filename: '' })}
      />

      {/* Delete Folder Confirmation */}
      <ConfirmDialog
        isOpen={deleteFolderConfirm.isOpen}
        title="Delete Folder"
        message={`Are you sure you want to delete folder "${deleteFolderConfirm.name}"?\n\nThis will also delete all documents in this folder.\n\nThis action cannot be undone.`}
        confirmText="Delete Folder"
        cancelText="Cancel"
        type="danger"
        onConfirm={confirmDeleteFolder}
        onCancel={() => setDeleteFolderConfirm({ isOpen: false, id: null, name: '' })}
      />

      {/* Create Folder Input Dialog */}
      <InputDialog
        isOpen={createFolderDialog.isOpen}
        title="Create New Folder"
        placeholder="Enter folder name..."
        confirmText="Create"
        cancelText="Cancel"
        onConfirm={confirmCreateFolder}
        onCancel={() => setCreateFolderDialog({ isOpen: false, parentId: null })}
      />

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}
