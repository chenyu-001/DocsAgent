import { useState, useEffect } from 'react'

const DEFAULT_TENANT_ID = '00000000-0000-0000-0000-000000000001'

interface DepartmentManagementProps {
  onError: (error: string) => void
}

interface Department {
  id: string
  name: string
  description?: string
  parent_id?: string
  manager_id?: number
  member_count: number
  children: Department[]
}

export default function DepartmentManagement({ onError }: DepartmentManagementProps) {
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(false)
  const [expandedDepts, setExpandedDepts] = useState<Set<string>>(new Set())

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [selectedDept, setSelectedDept] = useState<Department | null>(null)
  const [parentDept, setParentDept] = useState<Department | null>(null)

  // Form state
  const [deptForm, setDeptForm] = useState({
    name: '',
    description: '',
    parent_id: '',
    manager_id: ''
  })

  useEffect(() => {
    loadDepartments()
  }, [])

  const loadDepartments = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(`http://localhost:8000/api/tenants/current/departments`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': DEFAULT_TENANT_ID
        }
      })

      if (response.ok) {
        const data = await response.json()
        setDepartments(data.departments || [])
        // Expand root departments by default
        const rootIds = new Set(data.departments.map((d: Department) => d.id))
        setExpandedDepts(rootIds)
      } else {
        onError('Failed to load departments')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load departments')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateDepartment = async () => {
    if (!deptForm.name) {
      onError('请填写部门名称')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`http://localhost:8000/api/tenants/current/departments`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': DEFAULT_TENANT_ID,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: deptForm.name,
          description: deptForm.description || null,
          parent_id: deptForm.parent_id || null,
          manager_id: deptForm.manager_id ? parseInt(deptForm.manager_id) : null
        })
      })

      if (response.ok) {
        await loadDepartments()
        setShowCreateModal(false)
        setDeptForm({ name: '', description: '', parent_id: '', manager_id: '' })
        setParentDept(null)
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to create department')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to create department')
    }
  }

  const handleUpdateDepartment = async () => {
    if (!selectedDept) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/tenants/current/departments/${selectedDept.id}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name: deptForm.name || undefined,
            description: deptForm.description || undefined,
            manager_id: deptForm.manager_id ? parseInt(deptForm.manager_id) : undefined
          })
        }
      )

      if (response.ok) {
        await loadDepartments()
        setShowEditModal(false)
        setSelectedDept(null)
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to update department')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to update department')
    }
  }

  const handleDeleteDepartment = async () => {
    if (!selectedDept) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/tenants/current/departments/${selectedDept.id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID
          }
        }
      )

      if (response.ok) {
        await loadDepartments()
        setShowDeleteModal(false)
        setSelectedDept(null)
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to delete department')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to delete department')
    }
  }

  const toggleExpand = (deptId: string) => {
    setExpandedDepts(prev => {
      const newSet = new Set(prev)
      if (newSet.has(deptId)) {
        newSet.delete(deptId)
      } else {
        newSet.add(deptId)
      }
      return newSet
    })
  }

  const renderDepartmentTree = (dept: Department, level: number = 0) => {
    const isExpanded = expandedDepts.has(dept.id)
    const hasChildren = dept.children && dept.children.length > 0

    return (
      <div key={dept.id}>
        <div
          className="flex items-center py-2 px-4 hover:bg-gray-50 border-b border-gray-100"
          style={{ paddingLeft: `${level * 2 + 1}rem` }}
        >
          {/* Expand/Collapse Icon */}
          <button
            onClick={() => toggleExpand(dept.id)}
            className="w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600"
          >
            {hasChildren ? (
              isExpanded ? '▼' : '▶'
            ) : (
              <span className="text-gray-300">○</span>
            )}
          </button>

          {/* Department Info */}
          <div className="flex-1 ml-2">
            <div className="flex items-center">
              <span className="text-sm font-medium text-gray-900">{dept.name}</span>
              <span className="ml-2 text-xs text-gray-500">({dept.member_count}人)</span>
            </div>
            {dept.description && (
              <div className="text-xs text-gray-500 mt-1">{dept.description}</div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={() => {
                setParentDept(dept)
                setDeptForm({ name: '', description: '', parent_id: dept.id, manager_id: '' })
                setShowCreateModal(true)
              }}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              添加子部门
            </button>
            <button
              onClick={() => {
                setSelectedDept(dept)
                setDeptForm({
                  name: dept.name,
                  description: dept.description || '',
                  parent_id: '',
                  manager_id: dept.manager_id?.toString() || ''
                })
                setShowEditModal(true)
              }}
              className="text-xs text-green-600 hover:text-green-800"
            >
              编辑
            </button>
            <button
              onClick={() => {
                setSelectedDept(dept)
                setShowDeleteModal(true)
              }}
              className="text-xs text-red-600 hover:text-red-800"
            >
              删除
            </button>
          </div>
        </div>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div>
            {dept.children.map(child => renderDepartmentTree(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">部门管理</h2>
        <button
          onClick={() => {
            setParentDept(null)
            setDeptForm({ name: '', description: '', parent_id: '', manager_id: '' })
            setShowCreateModal(true)
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + 创建部门
        </button>
      </div>

      {/* Department Tree */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="px-6 py-8 text-center text-gray-500">加载中...</div>
        ) : departments.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500">
            暂无部门，点击上方按钮创建
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {departments.map(dept => renderDepartmentTree(dept))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">
              {parentDept ? `在 "${parentDept.name}" 下创建子部门` : '创建部门'}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  部门名称 *
                </label>
                <input
                  type="text"
                  value={deptForm.name}
                  onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="如：研发部"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  描述
                </label>
                <textarea
                  value={deptForm.description}
                  onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="部门职责描述（可选）"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  负责人 ID（可选）
                </label>
                <input
                  type="number"
                  value={deptForm.manager_id}
                  onChange={(e) => setDeptForm({ ...deptForm, manager_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="输入用户ID"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setParentDept(null)
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={handleCreateDepartment}
                className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedDept && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">编辑部门</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  部门名称 *
                </label>
                <input
                  type="text"
                  value={deptForm.name}
                  onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  描述
                </label>
                <textarea
                  value={deptForm.description}
                  onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  负责人 ID
                </label>
                <input
                  type="number"
                  value={deptForm.manager_id}
                  onChange={(e) => setDeptForm({ ...deptForm, manager_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setSelectedDept(null)
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={handleUpdateDepartment}
                className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && selectedDept && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">确认删除</h3>
            <p className="text-gray-600 mb-6">
              确定要删除部门 <strong>{selectedDept.name}</strong> 吗？
              <br />
              <span className="text-sm text-red-600">
                注意：删除前请确保该部门没有子部门和成员
              </span>
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowDeleteModal(false)
                  setSelectedDept(null)
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={handleDeleteDepartment}
                className="px-4 py-2 text-white bg-red-600 rounded-lg hover:bg-red-700"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
