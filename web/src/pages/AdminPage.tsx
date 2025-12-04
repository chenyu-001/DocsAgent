import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/client'
import type { User, Tenant } from '../api/types'
import UserManagement from '../components/admin/UserManagement'
import RoleManagement from '../components/admin/RoleManagement'
import DepartmentManagement from '../components/admin/DepartmentManagement'
import AuditLogViewer from '../components/admin/AuditLogViewer'

const DEFAULT_TENANT_ID = '00000000-0000-0000-0000-000000000001'

type TabType = 'tenant' | 'users' | 'roles' | 'departments' | 'audit'

export default function AdminPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('users')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Get current user
      const userData = await authApi.getCurrentUser()
      setUser(userData)

      // Check if user is platform admin
      if (!userData.is_platform_admin) {
        setError('You do not have admin permissions')
        return
      }

      const token = localStorage.getItem('access_token')

      // Get tenant info
      const tenantRes = await fetch(`http://localhost:8000/api/tenants/current/info`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': DEFAULT_TENANT_ID
        }
      })

      if (tenantRes.ok) {
        const tenantData: Tenant = await tenantRes.json()
        setTenant(tenantData)
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const handleError = (errorMsg: string) => {
    setError(errorMsg)
    setTimeout(() => setError(null), 5000)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">加载中...</div>
      </div>
    )
  }

  if (error && !user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="text-red-600 mb-4">{error}</div>
          <button
            onClick={() => navigate('/search')}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            返回首页
          </button>
        </div>
      </div>
    )
  }

  const tabs: { key: TabType; label: string; icon: string }[] = [
    { key: 'tenant', label: '租户概览', icon: '📊' },
    { key: 'users', label: '用户管理', icon: '👥' },
    { key: 'roles', label: '角色权限', icon: '🔐' },
    { key: 'departments', label: '部门管理', icon: '🏢' },
    { key: 'audit', label: '审计日志', icon: '📝' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">系统管理</h1>
              <p className="text-sm text-gray-600 mt-1">
                {user?.username} ({user?.platform_role})
              </p>
            </div>
            <button
              onClick={() => navigate('/search')}
              className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
            >
              返回首页
            </button>
          </div>
        </div>
      </header>

      {/* Error Toast */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
            <span className="block sm:inline">{error}</span>
            <button
              onClick={() => setError(null)}
              className="absolute top-0 bottom-0 right-0 px-4 py-3"
            >
              <span className="text-2xl">&times;</span>
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* Tenant Overview Tab */}
            {activeTab === 'tenant' && tenant && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">租户信息</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">租户名称</div>
                    <div className="text-lg font-medium text-gray-900">{tenant.name}</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">标识</div>
                    <div className="text-lg font-mono text-gray-900">{tenant.slug}</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">部署模式</div>
                    <div className="text-lg font-medium text-gray-900">{tenant.deploy_mode}</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">状态</div>
                    <div>
                      <span className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                        tenant.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {tenant.status}
                      </span>
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">用户数</div>
                    <div className="text-lg font-medium text-gray-900">
                      {tenant.user_count} / {tenant.user_quota}
                    </div>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${Math.min((tenant.user_count / tenant.user_quota) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">文档数</div>
                    <div className="text-lg font-medium text-gray-900">
                      {tenant.document_count} / {tenant.document_quota}
                    </div>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${Math.min((tenant.document_count / tenant.document_quota) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="col-span-2 bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-2">存储使用</div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="font-medium">{formatBytes(tenant.storage_used_bytes)}</span>
                      <span className="text-gray-600">{formatBytes(tenant.storage_quota_bytes)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full transition-all ${
                          tenant.storage_usage_percent > 80 ? 'bg-red-600' :
                          tenant.storage_usage_percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                        }`}
                        style={{ width: `${Math.min(tenant.storage_usage_percent, 100)}%` }}
                      />
                    </div>
                    <div className="text-sm text-gray-600 mt-2">
                      {tenant.storage_usage_percent.toFixed(2)}% 已使用
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* User Management Tab */}
            {activeTab === 'users' && (
              <UserManagement onError={handleError} />
            )}

            {/* Role Management Tab */}
            {activeTab === 'roles' && (
              <RoleManagement onError={handleError} />
            )}

            {/* Department Management Tab */}
            {activeTab === 'departments' && (
              <DepartmentManagement onError={handleError} />
            )}

            {/* Audit Log Tab */}
            {activeTab === 'audit' && (
              <AuditLogViewer onError={handleError} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
