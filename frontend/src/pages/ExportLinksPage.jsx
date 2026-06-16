import { useState, useEffect } from 'react'
import { Download, Link } from 'lucide-react'
import { useAuthStore } from '../store/auth'
import api from '../api/client'
import { Button, Card } from '../components/shared/UI'

export default function ExportLinksPage() {
  const { user, selectedStore } = useAuthStore()
  const isAdmin = user?.is_admin

  const [status, setStatus]         = useState('publish')
  const [dateAfter, setDateAfter]   = useState('')
  const [dateBefore, setDateBefore] = useState('')
  const [targetUser, setTargetUser] = useState('0')
  const [users, setUsers]           = useState([])
  const [loading, setLoading]       = useState(false)
  const [result, setResult]         = useState(null)
  const [error, setError]           = useState('')

  useEffect(() => {
    if (isAdmin) {
      api.get('/admin/users').then(r => setUsers(r.data)).catch(() => {})
    }
  }, [])

  const handleExport = async () => {
    setLoading(true); setError(''); setResult(null)
    try {
      const params = {
        store_id:       selectedStore?.id || 0,
        status,
        date_after:     dateAfter,
        date_before:    dateBefore,
        target_user_id: isAdmin ? parseInt(targetUser) : 0,
      }
      const r = await api.get('/products/export-urls', { params })
      setResult(r.data)
    } catch(e) {
      setError(e.response?.data?.detail || 'Lỗi export')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (!result?.urls?.length) return
    const content = result.urls.join('\n')
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const storeName = selectedStore?.name || 'store'
    const date = new Date().toISOString().split('T')[0]
    a.download = `${storeName}_links_${status}_${date}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Export Links</h1>
        <p className="text-sm text-gray-500 mt-1">Xuất danh sách URL sản phẩm ra file TXT</p>
      </div>

      <Card className="p-6 space-y-4">
        {/* Store info */}
        {selectedStore && (
          <div className="flex items-center gap-2 text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-lg">
            <Link size={14}/>
            <span>Store: <strong>{selectedStore.name}</strong> — {selectedStore.wc_url}</span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          {/* Status */}
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Trạng thái SP</label>
            <select value={status} onChange={e => setStatus(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 bg-white">
              <option value="publish">Published</option>
              <option value="draft">Draft</option>
              <option value="any">Tất cả</option>
            </select>
          </div>

          {/* Admin: chọn user */}
          {isAdmin && (
            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">Lọc theo User</label>
              <select value={targetUser} onChange={e => setTargetUser(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 bg-white">
                <option value="0">Tất cả user</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.username}</option>
                ))}
              </select>
            </div>
          )}

          {/* Date after */}
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Từ ngày</label>
            <input type="date" value={dateAfter} onChange={e => setDateAfter(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"/>
          </div>

          {/* Date before */}
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Đến ngày</label>
            <input type="date" value={dateBefore} onChange={e => setDateBefore(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"/>
          </div>
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <Button onClick={handleExport} disabled={loading} size="lg" className="w-full">
          {loading ? '⏳ Đang lấy dữ liệu...' : '🔍 Lấy danh sách links'}
        </Button>
      </Card>

      {result && (
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-gray-900">Kết quả</p>
              <p className="text-sm text-gray-500">Tổng: <strong className="text-blue-600">{result.total}</strong> sản phẩm</p>
            </div>
            <Button onClick={handleDownload} disabled={!result.urls?.length}>
              <Download size={16}/> Tải file TXT
            </Button>
          </div>

          {/* Preview 10 links đầu */}
          {result.urls?.length > 0 && (
            <div className="bg-gray-900 rounded-lg p-3 max-h-60 overflow-y-auto">
              {result.urls.slice(0, 20).map((url, i) => (
                <div key={i} className="text-green-400 text-xs font-mono truncate">{url}</div>
              ))}
              {result.urls.length > 20 && (
                <div className="text-gray-500 text-xs mt-1">... và {result.urls.length - 20} links nữa</div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
