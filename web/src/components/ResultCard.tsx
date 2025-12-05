import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import type { SearchResult } from '../api/types'

interface ResultCardProps {
  result: SearchResult
  index: number
}

export default function ResultCard({ result, index }: ResultCardProps) {
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState(false)

  // Convert score to percentage
  const similarityPercent = Math.round(result.score * 100)

  // Get color based on score
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50'
    if (score >= 0.6) return 'text-blue-600 bg-blue-50'
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50'
    return 'text-gray-600 bg-gray-50'
  }

  const shouldTruncate = result.text.length > 300
  const displayText = expanded || !shouldTruncate
    ? result.text
    : result.text.substring(0, 300)

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex flex-col gap-1 flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-blue-600 flex-shrink-0" />
            <span className="text-sm font-medium text-gray-900">
              Result #{index + 1}
            </span>
          </div>
          {result.filename && (
            <div className="flex items-start gap-2 text-xs text-gray-600 ml-7">
              <span className="font-medium truncate" title={result.filename}>
                📄 {result.filename}
              </span>
              {result.folder_path && (
                <span className="text-gray-500 flex-shrink-0" title={result.folder_path}>
                  ({result.folder_path})
                </span>
              )}
            </div>
          )}
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium flex-shrink-0 ${getScoreColor(result.score)}`}>
          {similarityPercent}% 相关
        </div>
      </div>

      {/* Content */}
      <div className="text-gray-700 text-sm leading-relaxed">
        {displayText}
        {!expanded && shouldTruncate && (
          <span className="text-gray-400">...</span>
        )}
      </div>

      {/* Actions */}
      <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {shouldTruncate && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
            >
              {expanded ? (
                <>
                  <ChevronUp className="w-3 h-3" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="w-3 h-3" />
                  Show more
                </>
              )}
            </button>
          )}
          <button
            onClick={() => navigate(`/document/${result.document_id}`)}
            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
          >
            <ExternalLink className="w-3 h-3" />
            View full document
          </button>
        </div>
        <div className="text-xs text-gray-500">
          Score: {result.score.toFixed(4)}
        </div>
      </div>
    </div>
  )
}
