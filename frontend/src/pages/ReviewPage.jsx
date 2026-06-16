import { useState, useEffect } from 'react'
import { Star, Search, Play } from 'lucide-react'
import { getProducts, getReviewCounts, startReviewStore } from '../api/client'
import { useAuthStore } from '../store/auth'
import api from '../api/client'
import { useJobPoller } from '../hooks/useJobPoller'
import { Button, Card, Input, Badge, LogBox, Spinner } from '../components/shared/UI'

export default function ReviewPage() {
  const { selectedStore } = useAuthStore()
  const [products, setProducts]       = useState([])
  const [allProducts, setAllProducts] = useState([])
  const [reviewCounts, setReviewCounts] = useState({})
  const [loading, setLoading]         = useState(false)
  const [search, setSearch]           = useState('')
  const [page, setPage]               = useState(1)
  const [totalPages, setTotalPages]   = useState(1)
  const [selected, setSelected]       = useState(new Set())
  const [jobId, setJobId]             = useState(null)
  const [submitting, setSubmitting]   = useState(false)
  const [skipHasReview, setSkipHasReview] = useState(true)
  const [hideHasReview, setHideHasReview] = useState(false)

  const [useRange, setUseRange]     = useState(false)
  const [reviewCount, setReviewCount] = useState(15)
  const [countMin, setCountMin]     = useState(10)
  const [countMax, setCountMax]     = useState(20)
  const [startDate, setStartDate]   = useState(() => { const d = new Date(); d.setDate(d.getDate()-30); return d.toISOString().split('T')[0] })
  const [endDate, setEndDate]       = useState(() => new Date().toISOString().split('T')[0])
  const [dist5, setDist5]           = useState(90)
  const [dist4, setDist4]           = useState(10)
  const [dist3, setDist3]           = useState(0)
  const [delay, setDelay]           = useState(1.5)

  const { status: jobStatus, log, result } = useJobPoller(jobId)

  const fetchProducts = async (p = 1, q = '') => {
    setLoading(true)
    try {
      const data = await getProducts({ page: p, per_page: 50, search: q, store_id: selectedStore?.id || 0 })
      setAllProducts(data.products || [])
      setTotalPages(data.total_pages || 1)
      // Fetch review counts
      const ids = (data.products || []).map(p => p.id)
      if (ids.length > 0) {
        getReviewCounts(ids, selectedStore?.id || 0).then(counts => setReviewCounts(counts)).catch(() => {})
      }
    } finally { setLoading(false) }
  }

  useEffect(() => { if (selectedStore) { setPage(1); fetchProducts(1, '') } }, [selectedStore])
  useEffect(() => { if (selectedStore) fetchProducts(page, search) }, [page])

  useEffect(() => {
    if (hideHasReview) setProducts(allProducts.filter(p => !reviewCounts[String(p.id)] || reviewCounts[String(p.id)] === 0))
    else setProducts(allProducts)
  }, [allProducts, reviewCounts, hideHasReview])

  const handleSearch = (e) => { e.preventDefault(); setPage(1); fetchProducts(1, search) }
  const toggleSelect = (id) => {
    setSelected(prev => { const s = new Set(prev); s.has(id) ? s.delete(id) : s.add(id); return s })
  }
  const selectAll = () => setSelected(new Set(products.map(p => p.id)))
  const clearAll  = () => setSelected(new Set())

  const totalDist = parseInt(dist5) + parseInt(dist4) + parseInt(dist3)

  const handleStart = async () => {
    if (totalDist !== 100) { alert('Tổng phần trăm rating phải = 100%'); return }
    setSubmitting(true)
    try {
      const { job_id } = await startReviewStore({
        product_ids: Array.from(selected),
        review_count: reviewCount,
        review_count_min: useRange ? countMin : null,
        review_count_max: useRange ? countMax : null,
        start_date: startDate, end_date: endDate,
        dist_5: parseInt(dist5), dist_4: parseInt(dist4), dist_3: parseInt(dist3),
        delay_between: parseFloat(delay),
        skip_has_review: skipHasReview,
      }, selectedStore?.id || 0)
      setJobId(job_id)
    } catch (e) { alert('Lỗi: ' + (e.response?.data?.detail || e.message)) }
    finally { setSubmitting(false) }
  }

  const isRunning = jobStatus === 'running' || jobStatus === 'pending'

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Fake Review Generator</h1>
        <p className="text-sm text-gray-500 mt-1">AI tự động tạo review từ ảnh sản phẩm rồi import vào WooCommerce</p>
      </div>

      <Card className="p-6">
        <div className="flex gap-3 mb-3">
          <form onSubmit={handleSearch} className="flex gap-2 flex-1">
            <input type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Tìm sản phẩm..."
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand"/>
            <Button type="submit" variant="outline"><Search size={14}/> Tìm</Button>
          </form>
          <Button variant="ghost" onClick={selectAll} size="sm">Chọn tất cả</Button>
          <Button variant="ghost" onClick={clearAll} size="sm">Bỏ chọn</Button>
        </div>

        <div className="flex gap-4 mb-3 text-sm">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={hideHasReview} onChange={e => setHideHasReview(e.target.checked)} className="rounded"/>
            Ẩn SP đã có review
          </label>
        </div>

        {loading ? (
          <div className="flex justify-center py-8"><Spinner/></div>
        ) : (
          <div className="space-y-1 max-h-80 overflow-y-auto">
            {products.map(p => {
              const rc = reviewCounts[String(p.id)] || 0
              return (
                <label key={p.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input type="checkbox" checked={selected.has(p.id)} onChange={() => toggleSelect(p.id)} className="rounded"/>
                  {p.image && <img src={p.image} alt="" className="w-8 h-8 rounded object-cover"/>}
                  <span className="flex-1 text-sm truncate">{p.name}</span>
                  {rc > 0
                    ? <Badge variant="green">{rc} reviews</Badge>
                    : <Badge variant="gray">0 review</Badge>
                  }
                </label>
              )
            })}
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

      <Card className="p-6 space-y-5">
        <h2 className="font-semibold text-gray-900">Cấu hình Review</h2>

        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={useRange} onChange={e => setUseRange(e.target.checked)} className="rounded"/>
            Số review ngẫu nhiên theo khoảng
          </label>
          {useRange ? (
            <div className="grid grid-cols-2 gap-4">
              <Input label="Min" type="number" min="1" max="100" value={countMin} onChange={e => setCountMin(+e.target.value)}/>
              <Input label="Max" type="number" min="1" max="100" value={countMax} onChange={e => setCountMax(+e.target.value)}/>
            </div>
          ) : (
            <Input label="Số review mỗi sản phẩm" type="number" min="1" max="100" value={reviewCount} onChange={e => setReviewCount(+e.target.value)}/>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input label="Ngày bắt đầu" type="date" value={startDate} onChange={e => setStartDate(e.target.value)}/>
          <Input label="Ngày kết thúc" type="date" value={endDate} onChange={e => setEndDate(e.target.value)}/>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            Phân bố rating <span className={totalDist !== 100 ? 'text-red-500' : 'text-green-600'}>({totalDist}%)</span>
          </p>
          <div className="grid grid-cols-3 gap-4">
            {[['5★', dist5, setDist5], ['4★', dist4, setDist4], ['3★', dist3, setDist3]].map(([label, val, set]) => (
              <div key={label}>
                <label className="text-xs text-gray-600">{label}: {val}%</label>
                <input type="range" min="0" max="100" value={val} onChange={e => set(+e.target.value)} className="w-full accent-brand mt-1"/>
              </div>
            ))}
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-700">Delay giữa SP: {delay}s</label>
          <input type="range" min="1" max="10" step="0.5" value={delay} onChange={e => setDelay(+e.target.value)} className="w-full accent-brand mt-2"/>
        </div>

        <div className="flex items-center justify-between flex-wrap gap-3 pt-2 border-t border-gray-100">
          <div className="flex gap-4 text-sm">
            <p className="text-gray-600">Đã chọn: <strong className="text-brand">{selected.size} SP</strong>
              {selected.size === 0 && <span className="text-gray-400"> (= tất cả)</span>}
            </p>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={skipHasReview} onChange={e => setSkipHasReview(e.target.checked)} className="rounded"/>
              Bỏ qua SP đã có review
            </label>
          </div>
          <Button onClick={handleStart} disabled={submitting || isRunning} size="lg">
            {isRunning ? <><Spinner size="sm"/> Đang generate...</>
              : <><Play size={16}/> Bắt đầu Generate Review</>}
          </Button>
        </div>
      </Card>

      {jobId && (
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Tiến trình Review</h2>
            <Badge variant={jobStatus}>{jobStatus}</Badge>
          </div>
          <LogBox log={log}/>
          {result && (
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Tổng', value: result.total, color: 'text-gray-700' },
                { label: 'Done', value: result.done,  color: 'text-green-600' },
                { label: 'Lỗi',  value: result.failed, color: 'text-red-600' },
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
