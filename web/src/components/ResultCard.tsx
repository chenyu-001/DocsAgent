import { FileText } from 'lucide-react'
import type { SearchResult } from '../api/types'

interface ResultCardProps {
  result: SearchResult
  index: number
}

export default function ResultCard({ result, index }: ResultCardProps) {
  // Convert score to percentage
  const similarityPercent = Math.round(result.score * 100)

  // Get color based on score
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50'
    if (score >= 0.6) return 'text-blue-600 bg-blue-50'
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50'
    return 'text-gray-600 bg-gray-50'
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-blue-600" />
          <span className="text-sm font-medium text-gray-900">
            Result #{index + 1}
          </span>
          <span className="text-xs text-gray-500">
            Doc ID: {result.document_id}
          </span>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(result.score)}`}>
          {similarityPercent}% Match
        </div>
      </div>

      {/* Content */}
      <div className="text-gray-700 text-sm leading-relaxed">
        {result.text.length > 300 ? (
          <>
            {result.text.substring(0, 300)}
            <span className="text-gray-400">...</span>
          </>
        ) : (
          result.text
        )}
      </div>

      {/* Footer metadata */}
      <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
        <span>Chunk ID: {result.chunk_id}</span>
        <span>Score: {result.score.toFixed(4)}</span>
      </div>
    </div>
  )
}
