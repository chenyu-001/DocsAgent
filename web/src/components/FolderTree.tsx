import { useState } from 'react'
import { Folder, FolderOpen, Plus, Trash2, ChevronRight, ChevronDown } from 'lucide-react'

interface FolderNode {
  id: number
  name: string
  path: string
  children?: FolderNode[]
}

interface FolderTreeProps {
  folders: FolderNode[]
  selectedFolderId: number | null
  onSelectFolder: (folderId: number | null) => void
  onCreateFolder: (parentId: number | null) => void
  onDeleteFolder: (folderId: number, folderName: string) => void
}

function FolderTreeNode({
  folder,
  selectedFolderId,
  onSelectFolder,
  onCreateFolder,
  onDeleteFolder,
  level = 0,
}: {
  folder: FolderNode
  selectedFolderId: number | null
  onSelectFolder: (folderId: number | null) => void
  onCreateFolder: (parentId: number | null) => void
  onDeleteFolder: (folderId: number, folderName: string) => void
  level?: number
}) {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = folder.children && folder.children.length > 0
  const isSelected = selectedFolderId === folder.id

  return (
    <div>
      <div
        className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer group ${
          isSelected ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-100'
        }`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
      >
        {/* Expand/Collapse Icon */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-0.5 hover:bg-gray-200 rounded"
        >
          {hasChildren ? (
            expanded ? (
              <ChevronDown className="w-3 h-3" />
            ) : (
              <ChevronRight className="w-3 h-3" />
            )
          ) : (
            <div className="w-3 h-3" />
          )}
        </button>

        {/* Folder Icon and Name */}
        <div
          onClick={() => onSelectFolder(folder.id)}
          className="flex items-center gap-2 flex-1 min-w-0"
        >
          {isSelected ? (
            <FolderOpen className="w-4 h-4 flex-shrink-0" />
          ) : (
            <Folder className="w-4 h-4 flex-shrink-0" />
          )}
          <span className="text-sm truncate">{folder.name}</span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onCreateFolder(folder.id)
            }}
            className="p-1 hover:bg-gray-200 rounded"
            title="Create subfolder"
          >
            <Plus className="w-3 h-3" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDeleteFolder(folder.id, folder.name)
            }}
            className="p-1 hover:bg-red-100 rounded text-red-600"
            title="Delete folder"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Children */}
      {expanded && hasChildren && (
        <div>
          {folder.children!.map((child) => (
            <FolderTreeNode
              key={child.id}
              folder={child}
              selectedFolderId={selectedFolderId}
              onSelectFolder={onSelectFolder}
              onCreateFolder={onCreateFolder}
              onDeleteFolder={onDeleteFolder}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function FolderTree({
  folders,
  selectedFolderId,
  onSelectFolder,
  onCreateFolder,
  onDeleteFolder,
}: FolderTreeProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">Folders</h3>
        <button
          onClick={() => onCreateFolder(null)}
          className="p-1.5 hover:bg-gray-100 rounded text-blue-600"
          title="Create folder"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* All Documents */}
      <div
        onClick={() => onSelectFolder(null)}
        className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer mb-2 ${
          selectedFolderId === null ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-100'
        }`}
      >
        <Folder className="w-4 h-4" />
        <span className="text-sm font-medium">All Documents</span>
      </div>

      {/* Folder Tree */}
      <div className="space-y-0.5">
        {folders.map((folder) => (
          <FolderTreeNode
            key={folder.id}
            folder={folder}
            selectedFolderId={selectedFolderId}
            onSelectFolder={onSelectFolder}
            onCreateFolder={onCreateFolder}
            onDeleteFolder={onDeleteFolder}
          />
        ))}
      </div>

      {folders.length === 0 && (
        <div className="text-center py-6 text-gray-400 text-sm">
          No folders yet
          <br />
          <button
            onClick={() => onCreateFolder(null)}
            className="text-blue-600 hover:underline mt-2"
          >
            Create your first folder
          </button>
        </div>
      )}
    </div>
  )
}
