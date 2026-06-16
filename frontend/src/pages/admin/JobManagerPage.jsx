import { useState, useEffect, useCallback, useRef } from 'react'
import { RefreshCw, XCircle, Trash2, ChevronDown, ChevronUp } from 'lucide-react'
import api from '../../api/client'
import { Card, Button, Spinner } from '../../components/shared/UI'

const TYPE_LABEL  = { upload: 'Upload', seo: 'SEO', review: 'Review' }
const TYPE_COLOR  = { upload: 'bg-purple-100 text-purple-700', seo: 'bg-blue-100 text-blue-700', review: 'bg-pink-100 text-pink-700' }
const STATUS_LABEL = { pending: 'Chờ', running: 'Đang chạy', done: 'Xong', failed: 'Thất bại/Hủy' }
const STATUS_COLOR = {
  pending: 'bg-yellow-100 text-yellow-700',
  running: 'bg-blue-100 text-blue-700 animate-pulse',
  done:    'bg-green-100 text-green-700',
  failed:  'bg-red-100 text-red-700',
}

export default function JobManagerPage() {
  const [jobs, setJobs]           = useState([])
  const [filter, setFilter]       = useState({ type: '', status: '' })
  const [loading, setLoading]     = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const timerRef = useRef(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (filter.type)   params.job_type = filter.type
      if (filter.status) params.status   = filter.status
      const data = await api.get('/admin/jobs', { params }).then(r => r.data)
      setJobs(data)
    } catch(e) {}
    finally { setLoading(false) }
  }, [filter])

  useEffect(() => {
    load()
    timerRef.current = setInterval(load, 5000)
    return () => clearInterval(timerRef.current)
  }, [load])

  const retry = async (id) => {
    if (!confirm('Retry job này?')) return
    try {
      await api.post(`/admin/jobs/${id}/retry`)
      load()
    } catch(e) { alert(e.response?.data?.detail || 'Lỗi retry') }
  }

  const cancel = async (id) => {
    if (!confirm('Hủy job này?')) return
    await api.post(`/admin/jobs/${id}/cancel`).catch(() => {})
    load()
  }

  const remove = async (id) => {
    await api.delete(`/admin/jobs/${id}`).catch(() => {})
    setJobs(j => j.filter(x => x.id !== id))
  }

  const cancelAllPending = async () => {
    if (!confirm('Hủy tất cả jobs đang Chờ?')) return
    await api.post('/admin/jobs/cancel-all-pending',
      filter.type ? { job_type: filter.type } : {}
    ).catch(() => {})
    load()
  }

  const clearDone = async () => {
    if (!confirm('Xóa tất cả jobs Xong/Thất bại?')) return
    await api.delete('/admin/jobs/clear-done',
      { params: filter.type ? { job_type: filter.type } : {} }
    ).catch(() => {})
    load()
  }

  const pendingCount = jobs.filter(j => j.status === 'pending').length
  const runningCount = jobs.filter(j => j.status === 'running').length
  const doneCount    = jobs.filter(j => j.status === 'done' || j.status === 'failed').length

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Manager</h1>
          <p className="text-sm text-gray-500 mt-1">Quản lý tất cả tác vụ trong hệ thống</p>
        </div>
        <button onClick={load} className="text-gray-400 hover:text-gray-600 p-2">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''}/>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Tổng', value: jobs.length, color: 'bg-gray-100 text-gray-700' },
          { label: 'Đang chạy', value: runningCount, color: 'bg-blue-100 text-blue-700' },
          { label: 'Đang chờ', value: pendingCount, color: 'bg-yellow-100 text-yellow-700' },
          { label: 'Xong/Lỗi', value: doneCount, color: 'bg-green-100 text-green-700' },
        ].map(s => (
          <Card key={s.label} className="p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{s.value}</p>
            <p className="text-xs text-gray-500 mt-1">{s.label}</p>
          </Card>
        ))}
      </div>

      {/* Filters + Actions */}
      <div className="flex items-center gap-3 flex-wrap">
        <select value={filter.type} onChange={e => setFilter(f => ({...f, type: e.target.value}))}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand bg-white">
          <option value="">Tất cả loại</option>
          <option value="upload">Upload</option>
          <option value="seo">SEO</option>
          <option value="review">Review</option>
        </select>

        <select value={filter.status} onChange={e => setFilter(f => ({...f, status: e.target.value}))}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand bg-white">
          <option value="">Tất cả trạng thái</option>
          <option value="pending">Chờ</option>
          <option value="running">Đang chạy</option>
          <option value="done">Xong</option>
          <option value="failed">Thất bại</option>
        </select>

        <div className="ml-auto flex gap-2">
          {pendingCount > 0 && (
            <button onClick={cancelAllPending}
              className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg border border-red-300 text-red-600 hover:bg-red-50">
              <XCircle size={14}/> Hủy tất cả chờ ({pendingCount})
            </button>
          )}
          {doneCount > 0 && (
            <button onClick={clearDone}
              className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50">
              <Trash2 size={14}/> Xóa done/failed ({doneCount})
            </button>
          )}
        </div>
      </div>

      {/* Job List */}
      <Card className="overflow-hidden">
        {jobs.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">Không có job nào</div>
        ) : (
          <div className="divide-y divide-gray-100">
            {jobs.map(job => (
              <div key={job.id}>
                <div className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50">
                  {/* ID */}
                  <span className="text-xs text-gray-400 w-10 flex-shrink-0">#{job.id}</span>

                  {/* Type */}
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${TYPE_COLOR[job.job_type] || 'bg-gray-100 text-gray-600'}`}>
                    {TYPE_LABEL[job.job_type] || job.job_type}
                  </span>

                  {/* Status */}
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${STATUS_COLOR[job.status]}`}>
                    {STATUS_LABEL[job.status] || job.status}
                  </span>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700 truncate">
                      {job.filename || (job.sp_count > 0 ? `${job.sp_count} sản phẩm` : `Job #${job.id}`)}
                      {job.auto && <span className="ml-2 text-xs text-gray-400">auto-pipeline</span>}
                    </p>
                    <p className="text-xs text-gray-400">
                      {new Date(job.created_at).toLocaleString('vi-VN')}
                      {job.store_url && <span className="ml-2 text-blue-500 font-medium">{job.store_url.replace('https://', '')}</span>}
                      {job.uploader && <span className="ml-2 text-gray-400">· {job.uploader}</span>}
                    </p>
                  </div>

                  {/* SP count */}
                  {job.sp_count > 0 && (
                    <span className="text-xs text-gray-500 flex-shrink-0">{job.sp_count} SP</span>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {(job.status === 'failed') && (
                      <button onClick={() => retry(job.id)}
                        className="text-xs px-2 py-1 bg-blue-100 text-blue-600 rounded hover:bg-blue-200">
                        🔄 Retry
                      </button>
                    )}
                    {(job.status === 'pending' || job.status === 'running') && (
                      <button onClick={() => cancel(job.id)}
                        className="text-red-400 hover:text-red-600 p-1" title="Hủy">
                        <XCircle size={15}/>
                      </button>
                    )}
                    {(job.status === 'done' || job.status === 'failed') && (
                      <button onClick={() => remove(job.id)}
                        className="text-gray-400 hover:text-red-500 p-1" title="Xóa">
                        <Trash2 size={15}/>
                      </button>
                    )}
                    <button onClick={() => setExpandedId(expandedId === job.id ? null : job.id)}
                      className="text-gray-400 hover:text-gray-600 p-1">
                      {expandedId === job.id ? <ChevronUp size={15}/> : <ChevronDown size={15}/>}
                    </button>
                  </div>
                </div>

                {/* Expanded log */}
                {expandedId === job.id && (
                  <div className="px-4 pb-4 bg-gray-50 border-t border-gray-100 space-y-3">
                    {job.log_tail && (
                      <pre className="bg-gray-900 text-green-400 text-xs p-3 rounded-lg max-h-40 overflow-y-auto whitespace-pre-wrap font-mono mt-3">
                        {job.log_tail}
                      </pre>
                    )}
                    {job.result?.errors?.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-xs font-medium text-red-600">Lỗi:</p>
                        {job.result.errors.slice(0,5).map((e,i) => (
                          <p key={i} className="text-xs text-red-500">✗ {e.product}: {e.error}</p>
                        ))}
                      </div>
                    )}
                    {job.result?.product_urls?.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-xs font-medium text-green-600">SP đã xử lý ({job.result.product_urls.length}):</p>
                        {job.result.product_urls.slice(0,5).map((p,i) => (
                          <div key={i} className="flex items-center gap-2 text-xs">
                            <span className="text-green-500">✓</span>
                            <a href={p.url} target="_blank" rel="noopener noreferrer"
                               className="text-blue-600 hover:underline truncate">{p.title}</a>
                          </div>
                        ))}
                        {job.result.product_urls.length > 5 && (
                          <p className="text-xs text-gray-400">+{job.result.product_urls.length - 5} SP khác</p>
                        )}
                      </div>
                    )}
                    {!job.log_tail && !job.result && (
                      <p className="text-xs text-gray-400 mt-3">Không có thông tin thêm</p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
