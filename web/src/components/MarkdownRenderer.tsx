import { useMemo } from 'react'

interface MarkdownRendererProps {
  content: string
  className?: string
}

/**
 * Simple Markdown renderer for QA answers
 * Supports: bold, lists, line breaks, code blocks, and inline code
 */
export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  const renderMarkdown = useMemo(() => {
    if (!content) return null

    const lines = content.split('\n')
    const elements: JSX.Element[] = []
    let inCodeBlock = false
    let codeBlockLines: string[] = []
    let listItems: string[] = []
    let inList = false

    const flushCodeBlock = () => {
      if (codeBlockLines.length > 0) {
        elements.push(
          <pre key={elements.length} className="bg-gray-100 rounded p-3 my-2 overflow-x-auto">
            <code className="text-sm text-gray-800">{codeBlockLines.join('\n')}</code>
          </pre>
        )
        codeBlockLines = []
      }
    }

    const flushList = () => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={elements.length} className="list-disc list-inside space-y-1 my-2">
            {listItems.map((item, idx) => (
              <li key={idx} className="text-gray-800">
                {formatInlineMarkdown(item)}
              </li>
            ))}
          </ul>
        )
        listItems = []
      }
    }

    const formatInlineMarkdown = (text: string): React.ReactNode => {
      // Handle inline code `code`
      const parts: React.ReactNode[] = []
      let remaining = text
      let key = 0

      // Handle inline code
      const codeRegex = /`([^`]+)`/g
      let lastIndex = 0
      let match

      while ((match = codeRegex.exec(remaining)) !== null) {
        // Add text before match
        if (match.index > lastIndex) {
          const before = remaining.substring(lastIndex, match.index)
          parts.push(<span key={`text-${key++}`}>{formatBoldAndText(before)}</span>)
        }
        // Add code
        parts.push(
          <code key={`code-${key++}`} className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">
            {match[1]}
          </code>
        )
        lastIndex = match.index + match[0].length
      }

      // Add remaining text
      if (lastIndex < remaining.length) {
        parts.push(<span key={`text-${key++}`}>{formatBoldAndText(remaining.substring(lastIndex))}</span>)
      }

      return parts.length > 0 ? parts : formatBoldAndText(text)
    }

    const formatBoldAndText = (text: string): React.ReactNode => {
      // Handle bold **text**
      const boldRegex = /\*\*([^*]+)\*\*/g
      const parts: React.ReactNode[] = []
      let lastIndex = 0
      let match
      let key = 0

      while ((match = boldRegex.exec(text)) !== null) {
        // Add text before match
        if (match.index > lastIndex) {
          parts.push(text.substring(lastIndex, match.index))
        }
        // Add bold text
        parts.push(
          <strong key={`bold-${key++}`} className="font-semibold text-gray-900">
            {match[1]}
          </strong>
        )
        lastIndex = match.index + match[0].length
      }

      // Add remaining text
      if (lastIndex < text.length) {
        parts.push(text.substring(lastIndex))
      }

      return parts.length > 0 ? parts : text
    }

    lines.forEach((line, index) => {
      // Code blocks
      if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
          flushCodeBlock()
          inCodeBlock = false
        } else {
          flushList()
          inCodeBlock = true
        }
        return
      }

      if (inCodeBlock) {
        codeBlockLines.push(line)
        return
      }

      // Ordered lists (1. 2. 3.)
      if (/^\d+\.\s/.test(line.trim())) {
        if (inList && listItems.length > 0) {
          flushList()
        }
        const content = line.trim().replace(/^\d+\.\s/, '')
        if (!inList) {
          inList = true
          listItems = []
        }
        listItems.push(content)
        return
      }

      // Unordered lists (- or *)
      if (/^[-*]\s/.test(line.trim())) {
        if (!inList) {
          inList = true
          listItems = []
        }
        const content = line.trim().replace(/^[-*]\s/, '')
        listItems.push(content)
        return
      }

      // If we were in a list, flush it
      if (inList) {
        flushList()
        inList = false
      }

      // Headers
      if (line.startsWith('###')) {
        elements.push(
          <h3 key={elements.length} className="text-lg font-semibold text-gray-900 mt-4 mb-2">
            {formatInlineMarkdown(line.replace(/^###\s*/, ''))}
          </h3>
        )
        return
      }

      if (line.startsWith('##')) {
        elements.push(
          <h2 key={elements.length} className="text-xl font-semibold text-gray-900 mt-4 mb-2">
            {formatInlineMarkdown(line.replace(/^##\s*/, ''))}
          </h2>
        )
        return
      }

      if (line.startsWith('#')) {
        elements.push(
          <h1 key={elements.length} className="text-2xl font-bold text-gray-900 mt-4 mb-2">
            {formatInlineMarkdown(line.replace(/^#\s*/, ''))}
          </h1>
        )
        return
      }

      // Empty lines
      if (line.trim() === '') {
        elements.push(<div key={elements.length} className="h-2" />)
        return
      }

      // Regular paragraphs
      elements.push(
        <p key={elements.length} className="text-gray-800 leading-relaxed my-1">
          {formatInlineMarkdown(line)}
        </p>
      )
    })

    // Flush any remaining code block or list
    flushCodeBlock()
    flushList()

    return elements
  }, [content])

  return <div className={`markdown-content ${className}`}>{renderMarkdown}</div>
}
