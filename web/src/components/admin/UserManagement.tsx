import { useState, useEffect } from 'react'
import type { TenantUser, TenantRole } from '../../api/types'

const DEFAULT_TENANT_ID = '00000000-0000-0000-0000-000000000001'

interface UserManagementProps {
  onError: (error: string) => void
}

interface UserWithDetails extends TenantUser {
  username?: string
  email?: string
  full_name?: string
}

export default function UserManagement({ onError }: UserManagementProps) {
  const [users, setUsers] = useState<UserWithDetails[]>([])
  const [roles, setRoles] = useState<TenantRole[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [roleFilter, setRoleFilter] = useState<string>('all')

  // Modal states
  const [showEditModal, setShowEditModal] = useState(false)
  const [showRoleModal, setShowRoleModal] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UserWithDetails | null>(null)

  // Form states
  const [editForm, setEditForm] = useState({ full_name: '', email: '' })
  const [roleForm, setRoleForm] = useState({ role_name: '' })
  const [passwordForm, setPasswordForm] = useState({ new_password: '' })

  useEffect(() => {
    loadUsers()
    loadRoles()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await fetch(`http://localhost:8000/api/tenants/current/users`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': DEFAULT_TENANT_ID
        }
      })

      if (response.ok) {
        const data = await response.json()
        setUsers(data.users || [])
      } else {
        onError('Failed to load users')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const loadRoles = async () => {
    try {
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
      }
    } catch (err) {
      console.error('Failed to load roles', err)
    }
  }

  const handleUpdateUser = async () => {
    if (!selectedUser) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/tenants/current/users/${selectedUser.id}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(editForm)
        }
      )

      if (response.ok) {
        await loadUsers()
        setShowEditModal(false)
        setSelectedUser(null)
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to update user')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to update user')
    }
  }

  const handleUpdateRole = async () => {
    if (!selectedUser) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/tenants/current/users/${selectedUser.id}/role`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(roleForm)
        }
      )

      if (response.ok) {
        await loadUsers()
        setShowRoleModal(false)
        setSelectedUser(null)
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to update role')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to update role')
    }
  }

  const handleResetPassword = async () => {
    if (!selectedUser || passwordForm.new_password.length < 6) {
      onError('Password must be at least 6 characters')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/tenants/current/users/${selectedUser.id}/reset-password`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(passwordForm)
        }
      )

      if (response.ok) {
        setShowPasswordModal(false)
        setSelectedUser(null)
        setPasswordForm({ new_password: '' })
        alert('密码重置成功')
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to reset password')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to reset password')
    }
  }

  const handleToggleStatus = async (user: UserWithDetails) => {
    const newStatus = user.status === 'active' ? 'disabled' : 'active'

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/tenants/current/users/${user.id}/status`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ status: newStatus })
        }
      )

      if (response.ok) {
        await loadUsers()
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to update status')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to update status')
    }
  }

  const handleDeleteUser = async () => {
    if (!selectedUser) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/api/tenants/current/users/${selectedUser.id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID
          }
        }
      )

      if (response.ok) {
        await loadUsers()
        setShowDeleteModal(false)
        setSelectedUser(null)
      } else {
        const error = await response.json()
        onError(error.detail || 'Failed to delete user')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to delete user')
    }
  }

  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchTerm ||
      user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.full_name?.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus = statusFilter === 'all' || user.status === statusFilter
    const matchesRole = roleFilter === 'all' || user.role_name === roleFilter

    return matchesSearch && matchesStatus && matchesRole
  })

  return (
    <div>
      {/* Filters */}
      <div className="mb-6 flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="搜索用户名、邮箱、姓名..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">所有状态</option>
          <option value="active">正常</option>
          <option value="disabled">禁用</option>
        </select>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">所有角色</option>
          {roles.map(role => (
            <option key={role.id} value={role.name}>{role.display_name}</option>
          ))}
        </select>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                用户名
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                邮箱
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                角色
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                状态
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                  加载中...
                </td>
              </tr>
            ) : filteredUsers.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                  暂无用户数据
                </td>
              </tr>
            ) : (
              filteredUsers.map(user => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {user.username || user.user_id}
                    </div>
                    {user.full_name && (
                      <div className="text-sm text-gray-500">{user.full_name}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.email || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                      {user.role_name || '无角色'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      user.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {user.status === 'active' ? '正常' : '禁用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setSelectedUser(user)
                          setEditForm({
                            full_name: user.full_name || '',
                            email: user.email || ''
                          })
                          setShowEditModal(true)
                        }}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => {
                          setSelectedUser(user)
                          setRoleForm({ role_name: user.role_name || '' })
                          setShowRoleModal(true)
                        }}
                        className="text-purple-600 hover:text-purple-900"
                      >
                        角色
                      </button>
                      <button
                        onClick={() => {
                          setSelectedUser(user)
                          setShowPasswordModal(true)
                        }}
                        className="text-orange-600 hover:text-orange-900"
                      >
                        重置密码
                      </button>
                      <button
                        onClick={() => handleToggleStatus(user)}
                        className="text-yellow-600 hover:text-yellow-900"
                      >
                        {user.status === 'active' ? '禁用' : '启用'}
                      </button>
                      <button
                        onClick={() => {
                          setSelectedUser(user)
                          setShowDeleteModal(true)
                        }}
                        className="text-red-600 hover:text-red-900"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">编辑用户信息</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  姓名
                </label>
                <input
                  type="text"
                  value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  邮箱
                </label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setSelectedUser(null)
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={handleUpdateUser}
                className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Role Modal */}
      {showRoleModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">分配角色</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                选择角色
              </label>
              <select
                value={roleForm.role_name}
                onChange={(e) => setRoleForm({ role_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">请选择角色</option>
                {roles.map(role => (
                  <option key={role.id} value={role.name}>
                    {role.display_name} ({role.description})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowRoleModal(false)
                  setSelectedUser(null)
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

      {/* Password Modal */}
      {showPasswordModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">重置密码</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                新密码（至少6位）
              </label>
              <input
                type="password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ new_password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowPasswordModal(false)
                  setSelectedUser(null)
                  setPasswordForm({ new_password: '' })
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={handleResetPassword}
                className="px-4 py-2 text-white bg-orange-600 rounded-lg hover:bg-orange-700"
              >
                重置
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">确认删除</h3>
            <p className="text-gray-600 mb-6">
              确定要从租户中移除用户 <strong>{selectedUser.username || selectedUser.user_id}</strong> 吗？
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowDeleteModal(false)
                  setSelectedUser(null)
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={handleDeleteUser}
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
