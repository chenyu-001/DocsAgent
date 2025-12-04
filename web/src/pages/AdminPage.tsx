import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/client'
import type { User, Tenant, TenantUser } from '../api/types'

const DEFAULT_TENANT_ID = '00000000-0000-0000-0000-000000000001'

export default function AdminPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [tenantUsers, setTenantUsers] = useState<TenantUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Get current user
      const userRes = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${authApi.getToken()}`
        }
      })

      if (!userRes.ok) throw new Error('Failed to load user info')
      const userData: User = await userRes.json()
      setUser(userData)

      // Check if user is platform admin
      if (!userData.is_platform_admin) {
        setError('You do not have admin permissions')
        return
      }

      // Get tenant info
      const tenantRes = await fetch(`http://localhost:8000/api/tenants/current/info`, {
        headers: {
          'Authorization': `Bearer ${authApi.getToken()}`,
          'X-Tenant-ID': DEFAULT_TENANT_ID
        }
      })

      if (tenantRes.ok) {
        const tenantData: Tenant = await tenantRes.json()
        setTenant(tenantData)
      }

      // Get tenant users
      const usersRes = await fetch(`http://localhost:8000/api/tenants/current/users`, {
        headers: {
          'Authorization': `Bearer ${authApi.getToken()}`,
          'X-Tenant-ID': DEFAULT_TENANT_ID
        }
      })

      if (usersRes.ok) {
        const usersData: TenantUser[] = await usersRes.json()
        setTenantUsers(usersData)
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">加载中...</div>
      </div>
    )
  }

  if (error) {
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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tenant Info */}
        {tenant && (
          <div className="bg-white rounded-lg shadow mb-6">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">租户信息</h2>
            </div>
            <div className="px-6 py-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-600">租户名称：</span>
                  <span className="font-medium">{tenant.name}</span>
                </div>
                <div>
                  <span className="text-gray-600">标识：</span>
                  <span className="font-mono text-sm">{tenant.slug}</span>
                </div>
                <div>
                  <span className="text-gray-600">部署模式：</span>
                  <span className="font-medium">{tenant.deploy_mode}</span>
                </div>
                <div>
                  <span className="text-gray-600">状态：</span>
                  <span className={`px-2 py-1 rounded text-sm ${
                    tenant.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {tenant.status}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">用户数：</span>
                  <span className="font-medium">{tenant.user_count} / {tenant.user_quota}</span>
                </div>
                <div>
                  <span className="text-gray-600">文档数：</span>
                  <span className="font-medium">{tenant.document_count} / {tenant.document_quota}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-600">存储使用：</span>
                  <div className="mt-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span>{formatBytes(tenant.storage_used_bytes)}</span>
                      <span>{formatBytes(tenant.storage_quota_bytes)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          tenant.storage_usage_percent > 80 ? 'bg-red-600' :
                          tenant.storage_usage_percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                        }`}
                        style={{ width: `${Math.min(tenant.storage_usage_percent, 100)}%` }}
                      />
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {tenant.storage_usage_percent}% 已使用
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Users List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">租户用户列表</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    用户ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    角色
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    部门
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    加入时间
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tenantUsers.map((tu) => (
                  <tr key={tu.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {tu.user_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {tu.role_name || '无角色'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {tu.department_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        tu.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {tu.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(tu.joined_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {tenantUsers.length === 0 && (
            <div className="px-6 py-8 text-center text-gray-500">
              暂无用户数据
            </div>
          )}
        </div>

        {/* API Documentation Link */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-lg font-medium text-blue-900 mb-2">更多管理功能</h3>
          <p className="text-blue-700 mb-3">
            完整的管理功能可以通过 API 文档访问：
          </p>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            打开 API 文档 (Swagger UI)
          </a>
        </div>
      </main>
    </div>
  )
}
