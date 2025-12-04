import { useState, useEffect } from 'react'
import type { TenantRole } from '../../api/types'

const DEFAULT_TENANT_ID = '00000000-0000-0000-0000-000000000001'

interface RoleManagementProps {
  onError: (error: string) => void
}

// Permission constants (from backend)
const PERMISSIONS = {
  READ: 1,
  WRITE: 2,
  DELETE: 4,
  SHARE: 8,
  ADMIN: 16,
  DOWNLOAD: 32,
  COMMENT: 64,
  EXPORT: 128,
}

const PERMISSION_LABELS = {
  [PERMISSIONS.READ]: '查看',
  [PERMISSIONS.WRITE]: '编辑',
  [PERMISSIONS.DELETE]: '删除',
  [PERMISSIONS.SHARE]: '分享',
  [PERMISSIONS.ADMIN]: '管理',
  [PERMISSIONS.DOWNLOAD]: '下载',
  [PERMISSIONS.COMMENT]: '评论',
  [PERMISSIONS.EXPORT]: '导出',
}

export default function RoleManagement({ onError }: RoleManagementProps) {
  const [roles, setRoles] = useState<TenantRole[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedRole, setSelectedRole] = useState<TenantRole | null>(null)

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)

  // Form state
  const [roleForm, setRoleForm] = useState({
    name: '',
    display_name: '',
    description: '',
    permissions: 0
  })

  useEffect(() => {
    loadRoles()
  }, [])

  const loadRoles = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(`http://localhost:8000/api/tenants/current/roles`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': DEFAULT_TENANT_ID
        }
      })

      if (response.ok) {
        const data = await response.json()
        setRoles(data.roles || [])
      } else {
        onError('Failed to load roles')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load roles')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateRole = async () => {
    if (!roleForm.name || !roleForm.display_name) {
      onError('请填写角色名称和显示名称')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`http://localhost:8000/api/tenants/current/roles`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': DEFAULT_TENANT_ID,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(roleForm)
      })

      if (response.ok) {
        await loadRoles()
        setShowCreateModal(false)
        setRoleForm({ name: '', display_name: '', description: '', permissions: 0 })
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to create role')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to create role')
    }
  }

  const handleUpdateRole = async () => {
    if (!selectedRole) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/tenants/current/roles/${selectedRole.id}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            display_name: roleForm.display_name,
            description: roleForm.description,
            permissions: roleForm.permissions
          })
        }
      )

      if (response.ok) {
        await loadRoles()
        setShowEditModal(false)
        setSelectedRole(null)
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to update role')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to update role')
    }
  }

  const handleDeleteRole = async () => {
    if (!selectedRole) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/tenants/current/roles/${selectedRole.id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID
          }
        }
      )

      if (response.ok) {
        await loadRoles()
        setShowDeleteModal(false)
        setSelectedRole(null)
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to delete role')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to delete role')
    }
  }

  const togglePermission = (perm: number) => {
    setRoleForm(prev => ({
      ...prev,
      permissions: prev.permissions ^ perm
    }))
  }

  const hasPermission = (permissions: number, perm: number) => {
    return (permissions & perm) === perm
  }

  const getPermissionList = (permissions: number) => {
    return Object.entries(PERMISSION_LABELS)
      .filter(([perm]) => hasPermission(permissions, parseInt(perm)))
      .map(([, label]) => label)
      .join(', ') || '无'
  }

  const systemRoles = roles.filter(r => r.is_system)
  const customRoles = roles.filter(r => !r.is_system)

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">角色管理</h2>
        <button
          onClick={() => {
            setRoleForm({ name: '', display_name: '', description: '', permissions: 0 })
            setShowCreateModal(true)
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + 创建自定义角色
        </button>
      </div>

      {/* System Roles */}
      <div className="mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">系统预设角色（不可删除）</h3>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  角色名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  描述
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  权限等级
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {systemRoles.map(role => (
                <tr key={role.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{role.display_name}</div>
                    <div className="text-sm text-gray-500">{role.name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">{role.description}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    等级 {role.level}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => {
                        setSelectedRole(role)
                        setShowViewModal(true)
                      }}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      查看权限
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Custom Roles */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">自定义角色</h3>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loading ? (
            <div className="px-6 py-8 text-center text-gray-500">加载中...</div>
          ) : customRoles.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              暂无自定义角色，点击上方按钮创建
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    角色名称
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    描述
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    权限
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {customRoles.map(role => (
                  <tr key={role.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{role.display_name}</div>
                      <div className="text-sm text-gray-500">{role.name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{role.description || '-'}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500">
                        {getPermissionList(role.permissions)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedRole(role)
                            setRoleForm({
                              name: role.name,
                              display_name: role.display_name,
                              description: role.description || '',
                              permissions: role.permissions
                            })
                            setShowEditModal(true)
                          }}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          编辑
                        </button>
                        <button
                          onClick={() => {
                            setSelectedRole(role)
                            setShowDeleteModal(true)
                          }}
                          className="text-red-600 hover:text-red-900"
                        >
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">创建自定义角色</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  角色标识 (英文)
                </label>
                <input
                  type="text"
                  value={roleForm.name}
                  onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })}
                  placeholder="例如: reviewer"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  显示名称
                </label>
                <input
                  type="text"
                  value={roleForm.display_name}
                  onChange={(e) => setRoleForm({ ...roleForm, display_name: e.target.value })}
                  placeholder="例如: 审阅者"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  描述
                </label>
                <textarea
                  value={roleForm.description}
                  onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  权限配置
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(PERMISSION_LABELS).map(([perm, label]) => (
                    <label key={perm} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={hasPermission(roleForm.permissions, parseInt(perm))}
                        onChange={() => togglePermission(parseInt(perm))}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setRoleForm({ name: '', display_name: '', description: '', permissions: 0 })
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={handleCreateRole}
                className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedRole && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">编辑角色</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  角色标识 (不可修改)
                </label>
                <input
                  type="text"
                  value={roleForm.name}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  显示名称
                </label>
                <input
                  type="text"
                  value={roleForm.display_name}
                  onChange={(e) => setRoleForm({ ...roleForm, display_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  描述
                </label>
                <textarea
                  value={roleForm.description}
                  onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  权限配置
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(PERMISSION_LABELS).map(([perm, label]) => (
                    <label key={perm} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={hasPermission(roleForm.permissions, parseInt(perm))}
                        onChange={() => togglePermission(parseInt(perm))}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setSelectedRole(null)
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={handleUpdateRole}
                className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Modal */}
      {showViewModal && selectedRole && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">角色权限详情</h3>
            <div className="space-y-4">
              <div>
                <span className="text-sm font-medium text-gray-700">角色名称：</span>
                <span className="text-sm text-gray-900">{selectedRole.display_name}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-700">权限列表：</span>
                <div className="mt-2 space-y-1">
                  {Object.entries(PERMISSION_LABELS).map(([perm, label]) => (
                    <div key={perm} className="flex items-center">
                      <span className={`w-4 h-4 rounded ${
                        hasPermission(selectedRole.permissions, parseInt(perm))
                          ? 'bg-green-500'
                          : 'bg-gray-300'
                      }`} />
                      <span className="ml-2 text-sm text-gray-700">{label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => {
                  setShowViewModal(false)
                  setSelectedRole(null)
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && selectedRole && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">确认删除</h3>
            <p className="text-gray-600 mb-6">
              确定要删除角色 <strong>{selectedRole.display_name}</strong> 吗？
              <br />
              <span className="text-sm text-gray-500">注意：已分配此角色的用户将无法继续使用</span>
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowDeleteModal(false)
                  setSelectedRole(null)
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={handleDeleteRole}
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
