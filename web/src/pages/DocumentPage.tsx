import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { documentApi, folderApi, authApi } from '../api/client'
import { Upload, ArrowLeft, FileText, CheckCircle, AlertCircle, Loader, Folder } from 'lucide-react'
import ConfirmDialog from '../components/ConfirmDialog'

export default function DocumentPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null)
  const [folders, setFolders] = useState<any[]>([])
  // Get folder ID from navigation state, default to null
  const [selectedFolderId, setSelectedFolderId] = useState<number | null>(
    (location.state as any)?.folderId ?? null
  )
  const [showOverwriteConfirm, setShowOverwriteConfirm] = useState(false)
  const [overwriteMessage, setOverwriteMessage] = useState('')

  useEffect(() => {
    fetchFolders()
  }, [])

  const fetchFolders = async () => {
    try {
      const response = await folderApi.getTree()
      setFolders(flattenFolders(response))
    } catch (error) {
      console.error('Failed to fetch folders:', error)
    }
  }

  // Flatten folder tree for dropdown
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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
    }
  }

  const handleUpload = async (overwrite: boolean = false) => {
    if (!file) return

    setUploading(true)
    setProgress(0)
    setResult(null)
    setShowOverwriteConfirm(false)

    try {
      const response = await documentApi.upload(
        file,
        (prog) => {
          setProgress(prog)
        },
        selectedFolderId,
        overwrite
      )
      setResult({
        success: true,
        message: `Upload successful! Document processed into ${response.chunks} chunks`,
      })
      setFile(null)
      setUploading(false)
      setProgress(0)
    } catch (error: any) {
      console.error('Upload failed:', error)
      console.log('Error response:', error.response)
      console.log('Error response data:', error.response?.data)
      console.log('Error response detail:', error.response?.data?.detail)

      // Check if it's a file exists error (409 status)
      const detail = error.response?.data?.detail
      const isFileExists = error.response?.status === 409 &&
                          (detail?.code === 'FILE_EXISTS' ||
                           (typeof detail === 'object' && detail?.code === 'FILE_EXISTS'))

      if (isFileExists) {
        // Show confirmation dialog
        const message = detail?.message || "File already exists. Do you want to overwrite it?"
        setOverwriteMessage(message)
        setShowOverwriteConfirm(true)
        setUploading(false)
        setProgress(0)
      } else {
        // Other errors
        let errorMessage = 'Upload failed'

        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (detail?.message) {
          errorMessage = detail.message
        } else if (typeof detail === 'object') {
          errorMessage = JSON.stringify(detail)
        } else if (error.message) {
          errorMessage = error.message
        }

        setResult({
          success: false,
          message: errorMessage,
        })
        setUploading(false)
        setProgress(0)
      }
    }
  }

  const handleConfirmOverwrite = () => {
    handleUpload(true)
  }

  const handleCancelOverwrite = () => {
    setShowOverwriteConfirm(false)
    setResult({
      success: false,
      message: 'Upload cancelled',
    })
  }

  const handleLogout = () => {
    authApi.logout()
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/search')}
              className="flex items-center space-x-2 text-gray-700 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back to Search</span>
            </button>
            <button
              onClick={handleLogout}
              className="text-gray-700 hover:text-gray-900"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="text-center mb-8">
            <FileText className="w-16 h-16 text-blue-600 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Upload Document
            </h1>
            <p className="text-gray-600">
              Supported formats: PDF, Word, PowerPoint, Excel, TXT, Markdown
            </p>
          </div>

          {/* Folder Selection */}
          {folders.length > 0 && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <div className="flex items-center gap-2">
                  <Folder className="w-4 h-4" />
                  <span>Select Folder (Optional)</span>
                </div>
              </label>
              <select
                value={selectedFolderId || ''}
                onChange={(e) => setSelectedFolderId(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Root / No Folder</option>
                {folders.map((folder) => (
                  <option key={folder.id} value={folder.id}>
                    {'  '.repeat(folder.level)}
                    {folder.level > 0 && '└─ '}
                    {folder.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* File Selection */}
          <div className="mb-6">
            <label className="block w-full">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors cursor-pointer">
                {file ? (
                  <div>
                    <FileText className="w-12 h-12 text-blue-600 mx-auto mb-3" />
                    <p className="text-gray-900 font-medium">{file.name}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      {formatFileSize(file.size)}
                    </p>
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        setFile(null)
                      }}
                      className="mt-3 text-sm text-red-600 hover:underline"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <div>
                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600">Click to select file or drag and drop here</p>
                    <p className="text-sm text-gray-500 mt-2">
                      Maximum file size: 100MB
                    </p>
                  </div>
                )}
              </div>
              <input
                type="file"
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf,.docx,.pptx,.xlsx,.txt,.md,.html"
              />
            </label>
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {uploading ? (
              <span className="flex items-center justify-center">
                <Loader className="w-5 h-5 mr-2 animate-spin" />
                Uploading ({progress}%)
              </span>
            ) : (
              'Start Upload'
            )}
          </button>

          {/* Progress Bar */}
          {uploading && (
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Result Message */}
          {result && (
            <div
              className={`mt-6 p-4 rounded-lg flex items-start space-x-3 ${
                result.success
                  ? 'bg-green-50 text-green-800'
                  : 'bg-red-50 text-red-800'
              }`}
            >
              {result.success ? (
                <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <p className="font-medium">{result.message}</p>
                {result.success && (
                  <button
                    onClick={() => navigate('/search')}
                    className="mt-2 text-sm underline hover:no-underline"
                  >
                    Go to search
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Overwrite Confirmation Dialog */}
          <ConfirmDialog
            isOpen={showOverwriteConfirm}
            title="File Already Exists"
            message={overwriteMessage}
            confirmText="Overwrite"
            cancelText="Cancel"
            type="warning"
            onConfirm={handleConfirmOverwrite}
            onCancel={handleCancelOverwrite}
          />

          {/* Instructions */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              Processing Steps:
            </h3>
            <ol className="text-sm text-gray-600 space-y-2">
              <li className="flex items-start">
                <span className="font-medium text-blue-600 mr-2">1.</span>
                <span>Upload document to server</span>
              </li>
              <li className="flex items-start">
                <span className="font-medium text-blue-600 mr-2">2.</span>
                <span>Automatically parse document content</span>
              </li>
              <li className="flex items-start">
                <span className="font-medium text-blue-600 mr-2">3.</span>
                <span>Split text into semantic chunks</span>
              </li>
              <li className="flex items-start">
                <span className="font-medium text-blue-600 mr-2">4.</span>
                <span>Generate vectors and store in database</span>
              </li>
              <li className="flex items-start">
                <span className="font-medium text-blue-600 mr-2">5.</span>
                <span>Done! Ready to search</span>
              </li>
            </ol>
          </div>
        </div>
      </main>
    </div>
  )
}
