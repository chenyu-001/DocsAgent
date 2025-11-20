import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import ResultCard from '../components/ResultCard'
import { searchApi, authApi } from '../api/client'
import type { SearchResult } from '../api/types'
import { Upload, LogOut, FileText, FolderOpen } from 'lucide-react'

export default function SearchPage() {
  const navigate = useNavigate()
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [query, setQuery] = useState('')
  const [searched, setSearched] = useState(false)

  const handleSearch = async (searchQuery: string) => {
    setLoading(true)
    setQuery(searchQuery)
    setSearched(true)

    try {
      const response = await searchApi.search({
        query: searchQuery,
        top_k: 10,
      })
      setResults(response.results)
    } catch (error: any) {
      console.error('Search failed:', error)
      alert('Search failed: ' + (error.response?.data?.error || error.message))
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
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Search Results
              </h3>
              {!loading && (
                <span className="text-sm text-gray-500">
                  Found {results.length} results
                </span>
              )}
            </div>

            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
                <p className="mt-4 text-gray-600">Searching...</p>
              </div>
            ) : results.length > 0 ? (
              <div className="space-y-4">
                {results.map((result, index) => (
                  <ResultCard key={result.chunk_id} result={result} index={index} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600">
                  No results found
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  Try different keywords or upload relevant documents
                </p>
              </div>
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
