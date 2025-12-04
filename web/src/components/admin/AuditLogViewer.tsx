import { useState, useEffect } from 'react'

const DEFAULT_TENANT_ID = '00000000-0000-0000-0000-000000000001'

interface AuditLogViewerProps {
  onError: (error: string) => void
}

interface AuditLog {
  id: string
  action: string
  level: string
  username: string
  resource_type: string
  resource_name: string
  ip_address: string
  timestamp: string
  success: boolean
  details?: any
}

export default function AuditLogViewer({ onError }: AuditLogViewerProps) {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)

  // Filters
  const [filters, setFilters] = useState({
    action: '',
    level: '',
    user_id: '',
    start_date: '',
    end_date: ''
  })

  useEffect(() => {
    loadLogs()
  }, [page, filters])

  const loadLogs = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')

      // Build query string
      const params = new URLSearchParams({
        skip: ((page - 1) * pageSize).toString(),
        limit: pageSize.toString()
      })

      if (filters.action) params.append('action', filters.action)
      if (filters.level) params.append('level', filters.level)
      if (filters.user_id) params.append('user_id', filters.user_id)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)

      const response = await fetch(
        `http://localhost:8000/api/tenants/current/audit-logs?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setLogs(data.logs || [])
        setTotal(data.total || 0)
      } else {
        onError('Failed to load audit logs')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load audit logs')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const token = localStorage.getItem('access_token')

      // Build query string
      const params = new URLSearchParams({ format })
      if (filters.action) params.append('action', filters.action)
      if (filters.level) params.append('level', filters.level)
      if (filters.user_id) params.append('user_id', filters.user_id)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)

      const response = await fetch(
        `http://localhost:8000/api/tenants/current/audit-logs/export?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': DEFAULT_TENANT_ID
          }
        }
      )

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.${format}`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      } else {
        onError('Failed to export logs')
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to export logs')
    }
  }

  const handleResetFilters = () => {
    setFilters({
      action: '',
      level: '',
      user_id: '',
      start_date: '',
      end_date: ''
    })
    setPage(1)
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('zh-CN')
  }

  const getActionLabel = (action: string) => {
    const labels: { [key: string]: string } = {
      'user.login': '用户登录',
      'user.logout': '用户登出',
      'user.update': '更新用户',
      'user.delete': '删除用户',
      'user.disable': '禁用用户',
      'user.remove': '移除用户',
      'password.reset': '重置密码',
      'role.create': '创建角色',
      'role.update': '更新角色',
      'role.delete': '删除角色',
      'role.assign': '分配角色',
      'dept.create': '创建部门',
      'dept.update': '更新部门',
      'dept.delete': '删除部门',
      'doc.upload': '上传文档',
      'doc.delete': '删除文档',
    }
    return labels[action] || action
  }

  const getLevelColor = (level: string) => {
    const colors: { [key: string]: string } = {
      'info': 'bg-blue-100 text-blue-800',
      'warning': 'bg-yellow-100 text-yellow-800',
      'critical': 'bg-red-100 text-red-800',
      'security': 'bg-purple-100 text-purple-800'
    }
    return colors[level] || 'bg-gray-100 text-gray-800'
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">审计日志</h2>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('json')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            导出 JSON
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            导出 CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              操作类型
            </label>
            <select
              value={filters.action}
              onChange={(e) => setFilters({ ...filters, action: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">全部</option>
              <option value="user.login">用户登录</option>
              <option value="user.update">更新用户</option>
              <option value="user.disable">禁用用户</option>
              <option value="password.reset">重置密码</option>
              <option value="role.create">创建角色</option>
              <option value="role.update">更新角色</option>
              <option value="dept.create">创建部门</option>
              <option value="doc.upload">上传文档</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              级别
            </label>
            <select
              value={filters.level}
              onChange={(e) => setFilters({ ...filters, level: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">全部</option>
              <option value="info">信息</option>
              <option value="warning">警告</option>
              <option value="critical">关键</option>
              <option value="security">安全</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              开始时间
            </label>
            <input
              type="datetime-local"
              value={filters.start_date}
              onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              结束时间
            </label>
            <input
              type="datetime-local"
              value={filters.end_date}
              onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleResetFilters}
              className="w-full px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              重置筛选
            </button>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  时间
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  级别
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  用户
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  资源
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP地址
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  结果
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    加载中...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    暂无日志数据
                  </td>
                </tr>
              ) : (
                logs.map(log => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {getActionLabel(log.action)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getLevelColor(log.level)}`}>
                        {log.level}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.username || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>{log.resource_type || '-'}</div>
                      <div className="text-xs text-gray-400">{log.resource_name || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.ip_address || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        log.success
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {log.success ? '成功' : '失败'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                显示 {(page - 1) * pageSize + 1} 到 {Math.min(page * pageSize, total)} 条，共 {total} 条
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 border border-gray-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
                >
                  上一页
                </button>
                <span className="px-3 py-1 text-sm text-gray-700">
                  第 {page} / {totalPages} 页
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
                >
                  下一页
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
