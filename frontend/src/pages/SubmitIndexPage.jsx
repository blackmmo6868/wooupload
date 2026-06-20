import { useState } from 'react'
import { Send, ListChecks } from 'lucide-react'
import api from '../api/client'
import { Button, Card } from '../components/shared/UI'

export default function SubmitIndexPage() {
  const [urls, setUrls]       = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState('')

  const handleSubmit = async () => {
    if (!urls.trim()) return
    setLoading(true); setError(''); setResult(null)
    try {
      const r = await api.post('/gsc/submit', { urls })
      setResult(r.data)
      setUrls('')
    } catch (e) {
      setError(e.response?.data?.detail || 'Lỗi submit')
    } finally {
      setLoading(false)
    }
  }

  const lineCount = urls.split('\n').filter(l => l.trim()).length

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Submit Index</h1>
        <p className="text-sm text-gray-500 mt-1">Dán danh sách URL cần submit GSC indexing</p>
      </div>

      <Card className="p-6 space-y-4">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Danh sách URL {lineCount > 0 && <span className="text-gray-400">({lineCount} link)</span>}
          </label>
          <textarea
            value={urls}
            onChange={e => setUrls(e.target.value)}
            placeholder={'https://breaktees.com/product/abc/\nhttps://breaktees.com/product/xyz/'}
            rows={12}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 font-mono"
          />
          <p className="text-xs text-gray-400">Mỗi dòng 1 URL</p>
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <Button onClick={handleSubmit} disabled={loading || !urls.trim()} size="lg" className="w-full">
          {loading ? '⏳ Đang submit...' : <><Send size={16}/> Submit hàng đợi</>}
        </Button>
      </Card>

      {result && (
        <Card className="p-6 space-y-2">
          <div className="flex items-center gap-2">
            <ListChecks size={18} className="text-green-600"/>
            <p className="font-semibold text-gray-900">Kết quả</p>
          </div>
          <p className="text-sm text-gray-600">
            Đã thêm: <strong className="text-green-600">{result.added}</strong> link mới
            {result.skipped > 0 && <> — Bỏ qua (trùng): <strong className="text-gray-400">{result.skipped}</strong></>}
          </p>
        </Card>
      )}
    </div>
  )
}
