import type { Document as DocumentType } from '../api/types'

const STATUS_META: Record<
  DocumentType['status'],
  { label: string; className: string }
> = {
  ready: { label: 'Ready', className: 'bg-green-100 text-green-800' },
  parsing: { label: 'Parsing', className: 'bg-blue-100 text-blue-800' },
  embedding: { label: 'Embedding', className: 'bg-yellow-100 text-yellow-800' },
  uploading: { label: 'Uploading', className: 'bg-gray-100 text-gray-800' },
  failed: { label: 'Failed', className: 'bg-red-100 text-red-800' },
}

type Props = {
  status: DocumentType['status']
}

export function DocumentStatusBadge({ status }: Props) {
  const meta = STATUS_META[status] ?? {
    label: status,
    className: 'bg-gray-100 text-gray-800',
  }

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${meta.className}`}>
      {meta.label}
    </span>
  )
}
