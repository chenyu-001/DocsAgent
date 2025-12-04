import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import SearchBar from '../components/SearchBar'
import ResultCard from '../components/ResultCard'
import { MarkdownRenderer } from '../components/MarkdownRenderer'
import { qaApi, authApi, searchApi } from '../api/client'
import type { SearchResult, User } from '../api/types'
import { Upload, LogOut, FileText, FolderOpen, Settings } from 'lucide-react'

export default function SearchPage() {
  const navigate = useNavigate()
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [answer, setAnswer] = useState('')
  const [currentUser, setCurrentUser] = useState<User | null>(null)

  // Load current user info on mount
  useEffect(() => {
    loadUserInfo()
  }, [])

  const loadUserInfo = async () => {
    try {
      const user = await authApi.getCurrentUser()
      setCurrentUser(user)
    } catch (error) {
      console.error('Failed to load user info:', error)
    }
  }

  const handleSearch = async (searchQuery: string) => {
    setLoading(true)
    setSearched(true)
    setAnswer('')
    setResults([])

    try {
      const response = await qaApi.ask({
        question: searchQuery,
        top_k: 20, // Increased from 10 to get more comprehensive results
      })
      setAnswer(response.answer)
      setResults(response.sources)
    } catch (error: any) {
      console.error('Search failed:', error)

      if (axios.isAxiosError(error)) {
        // Handle timeout errors
        if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          setAnswer(
            '⏱️ **请求超时**\n\n' +
            'AI 处理时间过长，这可能是因为：\n' +
            '- 文档内容较多，需要更长时间分析\n' +
            '- LLM 服务响应较慢\n\n' +
            '**建议：**\n' +
            '1. 尝试提出更具体的问题\n' +
            '2. 稍后重试\n' +
            '3. 或使用下方的参考片段直接查看文档内容'
          )
          // Still try to get search results
          try {
            const fallback = await searchApi.search({ query: searchQuery, top_k: 10 })
            setResults(fallback.results)
          } catch (e) {
            console.error('Fallback search also failed:', e)
          }
        } else if (error.response?.status === 404) {
          // Backend may not yet expose the QA endpoint; fall back to plain search results
          const fallback = await searchApi.search({ query: searchQuery, top_k: 10 })
          setAnswer('智能回答暂不可用，以下为最相关的片段。')
          setResults(fallback.results)
        } else {
          const message =
            (error.response?.data as { detail?: string; error?: string })?.detail ||
            error.message ||
            'Unknown error'
          alert('搜索失败: ' + message)
        }
      } else {
        alert('搜索失败: 未知错误')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    authApi.logout()
  }

  const handleUpload = () => {
    navigate('/upload')
  }

  const handleMyDocuments = () => {
    navigate('/documents')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Navigation */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">DocsAgent</h1>
                <p className="text-sm text-gray-500">Document Understanding AI</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleMyDocuments}
                className="flex items-center space-x-2 px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
              >
                <FolderOpen className="w-4 h-4" />
                <span>My Documents</span>
              </button>
              <button
                onClick={handleUpload}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Upload className="w-4 h-4" />
                <span>Upload</span>
              </button>
              {/* Show Admin button only for platform admins */}
              {currentUser?.is_platform_admin && (
                <button
                  onClick={() => navigate('/admin')}
                  className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  <span>Admin</span>
                </button>
              )}
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Bar */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Search Documents
          </h2>
          <SearchBar onSearch={handleSearch} loading={loading} />
          <p className="text-sm text-gray-500 mt-2">
            Tip: Enter a question or keyword to find relevant content from uploaded documents
          </p>
        </div>

        {/* Search Results */}
        {searched && (
          <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">智能回答</h3>
              {!loading && (
                <span className="text-sm text-gray-500">
                  基于 {results.length} 条相关片段生成
                </span>
              )}
            </div>

            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
                <p className="mt-4 text-gray-600 font-medium">正在搜索文档并生成答案...</p>
                <p className="mt-2 text-sm text-gray-500">AI 正在分析文档内容，这可能需要 30-60 秒</p>
              </div>
            ) : (
              <>
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
                  {answer ? (
                    <MarkdownRenderer content={answer} />
                  ) : (
                    <p className="text-gray-600">未能生成回答，请重试或调整问题。</p>
                  )}
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-md font-semibold text-gray-900">参考来源</h4>
                    <span className="text-sm text-gray-500">按相关性排序</span>
                  </div>
                  {results.length > 0 ? (
                    <div className="space-y-4">
                      {results.map((result, index) => (
                        <ResultCard key={result.chunk_id} result={result} index={index} />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      未找到足够的参考内容来回答该问题。
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* Empty State */}
        {!searched && !loading && (
          <div className="text-center py-16">
            <FileText className="w-20 h-20 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Start Searching
            </h3>
            <p className="text-gray-600 mb-6">
              Enter a question or keyword above to find answers from your documents
            </p>
            <button
              onClick={handleUpload}
              className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Upload className="w-5 h-5" />
              <span>Upload some documents first</span>
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
