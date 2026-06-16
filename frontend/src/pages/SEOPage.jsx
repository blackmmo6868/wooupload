import { useState, useEffect } from 'react'
import { FileText, Search, Play } from 'lucide-react'
import { getProducts, startSeoStore } from '../api/client'
import { useAuthStore } from '../store/auth'
import api from '../api/client'
import { useJobPoller } from '../hooks/useJobPoller'
import { Button, Card, Badge, LogBox, Spinner } from '../components/shared/UI'

export default function SEOPage() {
  const { selectedStore } = useAuthStore()
  const [products, setProducts]     = useState([])
  const [allProducts, setAllProducts] = useState([])
  const [loading, setLoading]       = useState(false)
  const [search, setSearch]         = useState('')
  const [page, setPage]             = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [selected, setSelected]     = useState(new Set())
  const [skipExisting, setSkipExisting] = useState(true)
  const [hideHasDesc, setHideHasDesc]   = useState(false)
  const [jobId, setJobId]           = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const { status: jobStatus, log, result } = useJobPoller(jobId)

  const fetchProducts = async (p = 1, q = '') => {
    setLoading(true)
    try {
      const data = await getProducts({ page: p, per_page: 50, search: q, status: 'any', store_id: selectedStore?.id || 0 })
      setAllProducts(data.products || [])
      setTotalPages(data.total_pages || 1)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { if (selectedStore) { setPage(1); fetchProducts(1, '') } }, [selectedStore])
  useEffect(() => { if (selectedStore) fetchProducts(page, search) }, [page])

  useEffect(() => {
    if (hideHasDesc) setProducts(allProducts.filter(p => !p.has_desc))
    else setProducts(allProducts)
  }, [allProducts, hideHasDesc])

  const handleSearch = (e) => { e.preventDefault(); setPage(1); fetchProducts(1, search) }
  const toggleSelect = (id) => {
    setSelected(prev => { const s = new Set(prev); s.has(id) ? s.delete(id) : s.add(id); return s })
  }
  const selectAll = () => setSelected(new Set(products.map(p => p.id)))
  const clearAll  = () => setSelected(new Set())

  const handleStart = async () => {
    setSubmitting(true)
    try {
      const { job_id } = await startSeoStore({ product_ids: Array.from(selected), skip_existing: skipExisting }, selectedStore?.id || 0)
      setJobId(job_id)
    } catch (e) { alert('Lỗi: ' + (e.response?.data?.detail || e.message)) }
    finally { setSubmitting(false) }
  }

  const isRunning = jobStatus === 'running' || jobStatus === 'pending'

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">SEO Generator</h1>
        <p className="text-sm text-gray-500 mt-1">Tự động generate mô tả + Rank Math meta bằng AI</p>
      </div>

      <Card className="p-6">
        <div className="flex gap-3 mb-3">
          <form onSubmit={handleSearch} className="flex gap-2 flex-1">
            <input type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Tìm sản phẩm theo tên..."
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand"/>
            <Button type="submit" variant="outline"><Search size={14}/> Tìm</Button>
          </form>
          <Button variant="ghost" onClick={selectAll} size="sm">Chọn tất cả</Button>
          <Button variant="ghost" onClick={clearAll} size="sm">Bỏ chọn</Button>
        </div>

        <div className="flex gap-4 mb-3 text-sm">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={hideHasDesc} onChange={e => setHideHasDesc(e.target.checked)} className="rounded"/>
            Ẩn SP đã có mô tả
          </label>
        </div>

        {loading ? (
          <div className="flex justify-center py-8"><Spinner/></div>
        ) : (
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {products.map(p => (
              <label key={p.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input type="checkbox" checked={selected.has(p.id)} onChange={() => toggleSelect(p.id)} className="rounded"/>
                {p.image && <img src={p.image} alt="" className="w-8 h-8 rounded object-cover"/>}
                <span className="flex-1 text-sm text-gray-800 truncate">{p.name}</span>
                {p.has_desc ? <Badge variant="green">Có mô tả</Badge> : <Badge variant="gray">Chưa có</Badge>}
              </label>
            ))}
            {products.length === 0 && <p className="text-center text-gray-400 py-4 text-sm">Không có sản phẩm nào</p>}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex gap-2 mt-4 justify-center flex-wrap">
            {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => i + 1).map(p => (
              <button key={p} onClick={() => setPage(p)}
                className={`w-8 h-8 text-sm rounded ${p === page ? 'bg-brand text-white' : 'bg-gray-100 hover:bg-gray-200'}`}>{p}</button>
            ))}
          </div>
        )}
      </Card>

      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <p className="text-sm text-gray-600">
            Đã chọn: <strong className="text-brand">{selected.size} sản phẩm</strong>
            {selected.size === 0 && <span className="text-gray-400"> (chọn = xử lý tất cả)</span>}
          </p>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={skipExisting} onChange={e => setSkipExisting(e.target.checked)} className="rounded"/>
            Bỏ qua SP đã có mô tả khi chạy
          </label>
        </div>
        <Button onClick={handleStart} disabled={submitting || isRunning} size="lg">
          {isRunning ? <><Spinner size="sm"/> Đang generate SEO...</>
            : <><Play size={16}/> Bắt đầu Generate SEO</>}
        </Button>
      </Card>

      {jobId && (
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Tiến trình SEO</h2>
            <Badge variant={jobStatus}>{jobStatus}</Badge>
          </div>
          <LogBox log={log}/>
          {result && (
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: 'Tổng',    value: result.total,   color: 'text-gray-700' },
                { label: 'Done',    value: result.done,    color: 'text-green-600' },
                { label: 'Lỗi',     value: result.failed,  color: 'text-red-600' },
                { label: 'Bỏ qua', value: result.skipped, color: 'text-yellow-600' },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className={`text-2xl font-bold ${color}`}>{value ?? 0}</p>
                  <p className="text-xs text-gray-500">{label}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
