import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuthStore } from '../store/auth'
import { Upload, CheckCircle, Star, Search, X, ChevronDown, RefreshCw, Zap } from 'lucide-react'
import { getCategories, getCategoriesCached, getWcpaForms, getWcpaFormsCached, getBrands, getBrandsCached, startUpload } from '../api/client'
import api from '../api/client'
import { Button, Card, Select, Input, Spinner } from '../components/shared/UI'

const getJobQueue   = () => api.get('/jobs/my?limit=10').then(r => r.data)
const getJobLog     = (id) => api.get(`/jobs/${id}/log`).then(r => r.data)
const clearDoneJobs = () => api.delete('/jobs/clear-done').then(r => r.data)

const STATUS_LABEL = { pending: 'Chờ', running: 'Đang chạy', done: 'Xong', failed: 'Lỗi' }
const STATUS_CLASS  = {
  pending: 'bg-yellow-100 text-yellow-700',
  running: 'bg-blue-100 text-blue-700',
  done:    'bg-green-100 text-green-700',
  failed:  'bg-red-100 text-red-700',
}

function Toggle({ checked, onChange, disabled }) {
  return (
    <button type="button" onClick={() => !disabled && onChange(!checked)}
      className={`relative w-11 h-6 rounded-full transition-colors flex-shrink-0 ${
        disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'
      } ${checked && !disabled ? 'bg-brand' : 'bg-gray-300'}`}>
      <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
        checked && !disabled ? 'translate-x-5' : 'translate-x-0'
      }`}/>
    </button>
  )
}

function PipelineStep({ step, icon, title, desc, enabled, onToggle, disabled, disabledReason, children }) {
  return (
    <div className={`rounded-xl border-2 transition-all ${
      disabled ? 'border-gray-100 bg-gray-50 opacity-60'
      : enabled ? 'border-brand bg-blue-50'
      : 'border-gray-200 bg-white'
    }`}>
      <div className="flex items-center gap-3 p-4">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
          step === 1 ? 'bg-green-500 text-white'
          : enabled && !disabled ? 'bg-brand text-white'
          : 'bg-gray-200 text-gray-500'
        }`}>
          {step === 1 ? '✓' : step}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-lg">{icon}</span>
            <p className="font-semibold text-sm text-gray-900">{title}</p>
            {disabled && disabledReason && (
              <span className="text-xs text-gray-400 italic">— {disabledReason}</span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
        </div>
        {step > 1 && (
          <Toggle checked={enabled && !disabled} onChange={onToggle} disabled={disabled}/>
        )}
        {step === 1 && (
          <span className="text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded-full">Luôn bật</span>
        )}
      </div>
      {enabled && !disabled && children && (
        <div className="border-t border-blue-200 px-4 pb-4 pt-3 space-y-3">
          {children}
        </div>
      )}
    </div>
  )
}

function JobQueuePanel() {
  const [jobs, setJobs]             = useState([])
  const [expandedId, setExpandedId] = useState(null)
  const [logs, setLogs]             = useState({})
  const timerRef                    = useRef(null)

  const refresh = useCallback(async () => {
    try {
      const q = await getJobQueue()
      setJobs(q)
      // Auto fetch log của job đang running
      const running = q.find(j => j.status === 'running')
      if (running) {
        try {
          const d = await getJobLog(running.id)
          setLogs(prev => ({...prev, [running.id]: d.log || ''}))
          setExpandedId(running.id)
        } catch(e) {}
      }
    } catch(e) {}
  }, [])

  useEffect(() => {
    refresh()
    timerRef.current = setInterval(refresh, 3000)
    return () => clearInterval(timerRef.current)
  }, [])

  const toggle = async (id) => {
    if (expandedId === id) { setExpandedId(null); return }
    setExpandedId(id)
    try {
      const d = await getJobLog(id)
      setLogs(prev => ({...prev, [id]: d.log || ''}))
    } catch(e) {}
  }

  useEffect(() => {
    if (!expandedId) return
    const job = jobs.find(j => j.id === expandedId)
    if (job?.status !== 'running') return
    const t = setInterval(async () => {
      try {
        const d = await getJobLog(expandedId)
        setLogs(prev => ({...prev, [expandedId]: d.log || ''}))
      } catch(e) {}
    }, 2000)
    return () => clearInterval(t)
  }, [expandedId, jobs])

  const clearDone = async () => {
    try { await clearDoneJobs(); await refresh() } catch(e) {}
  }



  const activeCount = jobs.filter(j => j.status === 'pending' || j.status === 'running').length
  const doneCount   = jobs.filter(j => j.status === 'done' || j.status === 'failed').length

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="font-semibold text-sm text-gray-900">Hàng đợi</h2>
          {activeCount > 0 && (
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full animate-pulse">
              {activeCount} đang xử lý
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {doneCount > 0 && (
            <button onClick={clearDone}
              className="text-xs text-gray-500 hover:text-red-500 px-2 py-1 rounded border border-gray-200">
              Xóa lịch sử ({doneCount})
            </button>
          )}
          <button onClick={refresh} className="text-gray-400 hover:text-gray-600 p-1">
            <RefreshCw size={13}/>
          </button>
        </div>
      </div>
      <div className="space-y-2">
        {jobs.map(job => (
          <div key={job.id} className="border border-gray-100 rounded-lg overflow-hidden">
            <div onClick={() => toggle(job.id)}
              className="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-gray-50 select-none">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${STATUS_CLASS[job.status]}`}>
                {job.status === 'running' && '⟳ '}{STATUS_LABEL[job.status] || job.status}
              </span>
              <span className="flex-1 text-sm text-gray-700 truncate">
                {job.filename || `${job.job_type} #${job.id}`}
              </span>
              {job.status === 'done' && job.result && job.job_type === 'upload' && (
                <span className="text-xs text-green-600 flex-shrink-0 font-medium">
                  {job.result.successful || 0}/{job.result.total || 0} SP
                </span>
              )}
              <span className="text-gray-400 text-xs">{expandedId === job.id ? '▲' : '▼'}</span>
            </div>
            {expandedId === job.id && (
              <div className="border-t border-gray-100 p-3 bg-gray-50 space-y-2">
                <pre className="bg-gray-900 text-green-400 text-xs p-3 rounded-lg max-h-44 overflow-y-auto whitespace-pre-wrap font-mono">
                  {logs[job.id] || 'Đang tải...'}
                </pre>
                {job.result?.product_urls?.length > 0 && (
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {job.result.product_urls.map((p, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        <CheckCircle size={10} className="text-green-500 flex-shrink-0"/>
                        <a href={p.url} target="_blank" rel="noopener noreferrer"
                           className="text-blue-600 hover:underline truncate">{p.title}</a>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  )
}

export default function UploadPage() {
  const [file, setFile]               = useState(null)
  const [dragging, setDragging]       = useState(false)
  const [categories, setCategories]   = useState([])
  const [forms, setForms]             = useState([])
  const [brands, setBrands]           = useState([])
  const [submitting, setSubmitting]     = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [queued, setQueued]           = useState('')
  const [showPicker, setShowPicker]   = useState(false)
  const [catSearch, setCatSearch]     = useState('')
  const fileRef   = useRef()
  const pickerRef = useRef()

  const [status, setStatus]             = useState('draft')
  const [skuMode, setSkuMode]           = useState('random')
  const [price, setPrice]               = useState('')
  const [salePrice, setSalePrice]       = useState('')
  const [selectedCats, setSelectedCats] = useState([])
  const [primaryCatId, setPrimaryCatId] = useState(null)
  const [wcpaForm, setWcpaForm]         = useState('')
  const [skipDup, setSkipDup]           = useState(true)
  const [brandId, setBrandId]           = useState('')
  const [brandName, setBrandName]       = useState('')
  const [brandTaxonomy, setBrandTaxonomy] = useState('pwb-brand')
  const [tags, setTags]                 = useState([])
  const [tagInput, setTagInput]         = useState('')

  // Image processing
  const [imgEnabled, setImgEnabled]   = useState(false)
  const [skuPrefix, setSkuPrefix]       = useState('')
  const [imgMaxWidth, setImgMaxWidth] = useState(1000)
  const [imgQuality, setImgQuality]   = useState(75)
  const { user, selectedStore, setSelectedStore } = useAuthStore()
  const [stores, setStores]           = useState([])
  const [imgBrand, setImgBrand]       = useState('')
  useEffect(() => {
    if (selectedStore) {
      setImgBrand(selectedStore.store_name || selectedStore.name)
      const sid = selectedStore.id
      getCategoriesCached(sid).then(setCategories).catch(() => {})
      getWcpaFormsCached(sid).then(setForms).catch(() => {})
      getBrandsCached(sid).then(setBrands).catch(() => {})
    }
  }, [selectedStore])
  const [imgRating, setImgRating]     = useState(5)
  const [imgDays, setImgDays]         = useState(7)
  const [imgRename, setImgRename]     = useState(false)
  const [imgRenameMode, setImgRenameMode] = useState('classic')

  // Pipeline
  const [autoSeo, setAutoSeo]         = useState(false)
  const [autoPublish, setAutoPublish] = useState(false)
  const [autoReview, setAutoReview]   = useState(false)
  const [reviewCount, setReviewCount] = useState(15)
  const [useRange, setUseRange]       = useState(false)
  const [countMin, setCountMin]       = useState(10)
  const [countMax, setCountMax]       = useState(20)
  const [startDate, setStartDate]     = useState(() => { const d = new Date(); d.setDate(d.getDate()-30); return d.toISOString().split('T')[0] })
  const [endDate, setEndDate]         = useState(() => new Date().toISOString().split('T')[0])
  const [dist5, setDist5]             = useState(90)
  const [dist4, setDist4]             = useState(10)
  const [dist3, setDist3]             = useState(0)
  const [skipReview, setSkipReview]   = useState(true)

  useEffect(() => {
    // Load stores của user
    api.get('/auth/my-stores').then(r => {
      const s = r.data
      setStores(s)
      if (s.length === 1) setSelectedStore(s[0])
    }).catch(() => {})
    const sid = selectedStore?.id || 0
    getCategoriesCached(sid).then(setCategories).catch(() => {})
    getWcpaFormsCached(sid).then(setForms).catch(() => {})
    getBrandsCached(sid).then(b => { setBrands(b)
      const bt = b.find(x => x.name.toLowerCase().includes('breaktees'))
      if (bt) { setBrandId(String(bt.id)); setBrandName(bt.name) }
    }).catch(() => {})
  }, [selectedStore])

  useEffect(() => {
    const h = (e) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target)) setShowPicker(false)
    }
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])

  const onDrop = (e) => {
    e.preventDefault(); setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f?.name.endsWith('.zip') || f?.name.endsWith('.rar')) { setFile(f); setQueued('') }
  }

  const toggleCat = (cat) => {
    const exists = selectedCats.find(c => c.id === cat.id)
    if (exists) {
      const next = selectedCats.filter(c => c.id !== cat.id)
      setSelectedCats(next)
      if (primaryCatId === cat.id) setPrimaryCatId(next[0]?.id || null)
    } else {
      setSelectedCats(prev => [...prev, { id: cat.id, name: cat.name }])
      if (!primaryCatId) setPrimaryCatId(cat.id)
    }
  }

  const filteredCats = categories.filter(c =>
    c.name.toLowerCase().includes(catSearch.toLowerCase())
  )

  const totalPct    = dist5 + dist4 + dist3
  const canSubmit   = !!file && !submitting && (!autoReview || totalPct === 100)

  const handleToggleSeo     = (v) => { setAutoSeo(v); if (!v) { setAutoPublish(false); setAutoReview(false) } }
  const handleTogglePublish = (v) => { setAutoPublish(v); if (!v) setAutoReview(false) }

  const handleSubmit = async () => {
    if (!canSubmit) return
    setSubmitting(true); setQueued('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('store_id', selectedStore?.id || 0)
      fd.append('status', status)
      fd.append('sku_mode', skuMode)
      if (skuMode === 'prefix_random') fd.append('sku_prefix', skuPrefix)
      fd.append('regular_price', price)
      fd.append('sale_price', salePrice)
      fd.append('categories', JSON.stringify(selectedCats.map(c => c.id)))
      fd.append('primary_category_id', primaryCatId || '')
      fd.append('tags', JSON.stringify(tags))
      fd.append('wcpa_form_id', wcpaForm)
      fd.append('optimize_images', false)
      fd.append('skip_duplicates', skipDup)
      fd.append('brand_name', brandName)
      fd.append('brand_id', brandId)
      fd.append('brand_taxonomy', brandTaxonomy)
      fd.append('image_config', JSON.stringify({
        enabled:     imgEnabled,
        max_width:   imgMaxWidth,
        quality:     imgQuality,
        brand:       imgBrand,
        rating:      imgRating,
        date_days:   imgDays,
        rename_mode: imgEnabled && imgRename ? imgRenameMode : 'none',
      }))
      fd.append('pipeline_config', JSON.stringify({
        seo:     autoSeo,
        publish: autoPublish,
        review:  autoReview,
        review_config: {
          review_count:     reviewCount,
          review_count_min: useRange ? countMin : null,
          review_count_max: useRange ? countMax : null,
          start_date:  startDate,
          end_date:    endDate,
          dist_5:      dist5,
          dist_4:      dist4,
          dist_3:      dist3,
          skip_has_review: skipReview,
          delay_between:   1.5,
        }
      }))
      setUploadProgress(0)
      await startUpload(fd, (pct) => setUploadProgress(pct))
      setUploadProgress(0)
      setQueued(file.name)
      setFile(null)
      if (fileRef.current) fileRef.current.value = ''
    } catch (e) {
      alert('Lỗi: ' + (e.response?.data?.detail || e.message))
    } finally { setSubmitting(false) }
  }

  const handleSelectStore = (s) => {
    setSelectedStore(s)
    setSelectedCats([]); setWcpaForm(''); setBrandId(''); setBrands([]); setBrandTaxonomy('pwb-brand')
    setCategories([]); setForms([])
  }

  const storeSelector = stores.length > 1 ? (
    <div className="flex items-center gap-3 bg-white border border-gray-200 rounded-xl px-4 py-3">
      <label className="text-sm font-semibold text-gray-700 whitespace-nowrap">🏪 Store:</label>
      <select
        value={selectedStore?.id || ''}
        onChange={e => {
          const s = stores.find(x => x.id === parseInt(e.target.value))
          if (s) handleSelectStore(s)
        }}
        className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500">
        <option value="">-- Chọn store --</option>
        {stores.map(s => (
          <option key={s.id} value={s.id}>{s.name} — {s.wc_url.replace('https://', '')}</option>
        ))}
      </select>
      {!selectedStore && <p className="text-amber-500 text-xs whitespace-nowrap">⚠ Chọn store trước</p>}
    </div>
  ) : null

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {storeSelector}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload Sản Phẩm</h1>
        <p className="text-sm text-gray-500 mt-1">Submit nhiều file ZIP liên tiếp — tắt browser vẫn tiếp tục chạy</p>
      </div>

      <Card className="p-6 space-y-5">
        {/* Drop zone */}
        <div onClick={() => fileRef.current.click()}
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
            dragging ? 'border-brand bg-blue-50'
            : file    ? 'border-green-400 bg-green-50'
            : 'border-gray-300 hover:border-brand hover:bg-gray-50'
          }`}>
          <input ref={fileRef} type="file" accept=".zip,.rar" className="hidden"
            onChange={e => { const f = e.target.files[0]; if(f && (f.name.endsWith('.zip')||f.name.endsWith('.rar'))) { setFile(f); setQueued('') } }}/>
          <Upload size={32} className="mx-auto text-gray-400 mb-2"/>
          {file
            ? <p className="font-medium text-green-700">{file.name} ({(file.size/1024/1024).toFixed(1)} MB)</p>
            : <p className="text-gray-500 text-sm">Kéo thả hoặc click để chọn file ZIP / RAR</p>
          }
        </div>

        {submitting && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-500">
              <span>Đang tải file lên server...</span>
              <span className="font-medium">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-brand h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {queued && (
          <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-3">
            <CheckCircle size={16}/>
            <span><strong>"{queued}"</strong> đã vào hàng đợi!</span>
            <span className="ml-auto text-xs text-green-600">Chọn file tiếp theo nếu muốn ↑</span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <Select label="Trạng thái" value={status} onChange={e => setStatus(e.target.value)}>
            <option value="draft">Draft</option>
            <option value="publish">Publish</option>
            <option value="private">Private</option>
          </Select>
          <Select label="SKU" value={skuMode} onChange={e => setSkuMode(e.target.value)}>
            <option value="empty">Không có SKU</option>
            <option value="random">Random (ABC12345)</option>
            <option value="filename">Theo tên sản phẩm</option>
            <option value="prefix_random">Prefix + Random</option>
          </Select>
          {skuMode === 'prefix_random' && (
            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">
                SKU Prefix <span className="text-gray-400 font-normal text-xs">→ PREFIX-XXXXXXXX</span>
              </label>
              <input
                type="text"
                value={skuPrefix}
                onChange={e => setSkuPrefix(e.target.value.toUpperCase())}
                placeholder="VD: 3DTSHIRT"
                maxLength={20}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand font-mono"
              />
              {skuPrefix && (
                <p className="text-xs text-gray-400">
                  Preview: <span className="font-mono text-blue-600">{skuPrefix}-AB12CD34</span>
                </p>
              )}
            </div>
          )}
          <Input label="Giá bán" placeholder="24.99" value={price} onChange={e => setPrice(e.target.value)}/>
          <Input label="Giá sale" placeholder="19.99" value={salePrice} onChange={e => setSalePrice(e.target.value)}/>
        </div>

        {/* Category */}
        <div className="space-y-2" ref={pickerRef}>
          <label className="block text-sm font-medium text-gray-700">
            Danh mục
            {selectedCats.length > 0 && (
              <span className="ml-2 text-xs text-gray-400 font-normal">
                {selectedCats.length} đã chọn — click ⭐ để set primary
              </span>
            )}
          </label>
          {selectedCats.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {selectedCats.map(cat => (
                <div key={cat.id}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border ${
                    primaryCatId === cat.id ? 'bg-amber-50 border-amber-400 text-amber-700' : 'bg-gray-50 border-gray-300 text-gray-700'
                  }`}>
                  <button onClick={() => setPrimaryCatId(cat.id)}
                    className={primaryCatId === cat.id ? 'text-amber-500' : 'text-gray-300 hover:text-amber-400'}>
                    <Star size={12} fill={primaryCatId === cat.id ? 'currentColor' : 'none'}/>
                  </button>
                  <span>{cat.name}</span>
                  {primaryCatId === cat.id && <span className="text-amber-500 font-semibold">Primary</span>}
                  <button onClick={() => toggleCat(cat)} className="text-gray-400 hover:text-red-500 ml-0.5">
                    <X size={11}/>
                  </button>
                </div>
              ))}
            </div>
          )}
          <button onClick={() => setShowPicker(!showPicker)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg text-left text-gray-500 hover:border-brand bg-white flex items-center justify-between">
            <span>{selectedCats.length === 0 ? '-- Chọn danh mục --' : '+ Thêm danh mục'}</span>
            <ChevronDown size={14} className={showPicker ? 'rotate-180' : ''}/>
          </button>
          {showPicker && (
            <div className="border border-gray-200 rounded-lg shadow-lg bg-white z-10 relative">
              <div className="p-2 border-b border-gray-100">
                <div className="relative">
                  <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400"/>
                  <input value={catSearch} onChange={e => setCatSearch(e.target.value)}
                    placeholder="Tìm danh mục..." autoFocus
                    className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-brand"/>
                </div>
              </div>
              <div className="max-h-52 overflow-y-auto">
                {filteredCats.map(cat => {
                  const isSel = !!selectedCats.find(c => c.id === cat.id)
                  return (
                    <div key={cat.id} onClick={() => toggleCat(cat)}
                      className={`flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-gray-50 ${isSel ? 'bg-blue-50' : ''}`}>
                      <div className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 ${isSel ? 'bg-brand border-brand' : 'border-gray-300'}`}>
                        {isSel && <CheckCircle size={12} className="text-white" fill="white"/>}
                      </div>
                      <span className="flex-1 text-sm">{cat.name}</span>
                      {primaryCatId === cat.id && <span className="text-xs text-amber-500">⭐ Primary</span>}
                      {cat.count > 0 && <span className="text-xs text-gray-400">{cat.count}</span>}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Select label="WCPA Form" value={wcpaForm} onChange={e => setWcpaForm(e.target.value)}>
            <option value="">-- Không có --</option>
            {forms.map(f => <option key={f.id} value={f.id}>{f.title}</option>)}
          </Select>
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Brand</label>
            <select value={brandId}
              onChange={e => { setBrandId(e.target.value); const b = brands.find(x => String(x.id) === e.target.value); if(b) { setBrandName(b.name); setBrandTaxonomy(b.taxonomy || 'pwb-brand') } }}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand bg-white">
              <option value="">-- Không gán Brand --</option>
              {brands.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>
        </div>

        {/* ── Tags ── */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Tags sản phẩm</label>
          <div className="flex flex-wrap gap-1.5 p-2 border border-gray-300 rounded-lg min-h-[40px] bg-white">
            {tags.map((t, i) => (
              <span key={i} className="flex items-center gap-1 bg-brand text-white text-xs px-2 py-1 rounded-full">
                {t}
                <button type="button" onClick={() => setTags(tags.filter((_, j) => j !== i))}
                  className="hover:text-red-200 font-bold">×</button>
              </span>
            ))}
            <input
              type="text"
              value={tagInput}
              onChange={e => setTagInput(e.target.value)}
              onKeyDown={e => {
                if ((e.key === 'Enter' || e.key === ',') && tagInput.trim()) {
                  e.preventDefault()
                  const newTag = tagInput.trim().replace(/,$/, '')
                  if (newTag && !tags.includes(newTag)) setTags([...tags, newTag])
                  setTagInput('')
                } else if (e.key === 'Backspace' && !tagInput && tags.length) {
                  setTags(tags.slice(0, -1))
                }
              }}
              placeholder={tags.length ? '' : 'Nhập tag rồi Enter hoặc dấu phẩy...'}
              className="flex-1 min-w-[150px] text-sm outline-none bg-transparent py-0.5"
            />
          </div>
          <p className="text-xs text-gray-400">Enter hoặc dấu phẩy để thêm tag. Backspace để xóa tag cuối.</p>
        </div>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={skipDup} onChange={e => setSkipDup(e.target.checked)} className="rounded"/>
          Bỏ qua sản phẩm trùng (slug/title)
        </label>

        {/* ── Image Processing ── */}
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <div className="flex items-center gap-3 p-4 bg-gray-50">
            <span className="text-lg">🖼️</span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-800">Xử lý ảnh</p>
              <p className="text-xs text-gray-500">Nén + Resize + EXIF Metadata trước khi upload</p>
            </div>
            <Toggle checked={imgEnabled} onChange={setImgEnabled} disabled={false}/>
          </div>

          {imgEnabled && (
            <div className="p-4 space-y-4 border-t border-gray-200">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">Max width (px)</label>
                  <input type="number" value={imgMaxWidth} onChange={e => setImgMaxWidth(+e.target.value)}
                    min={400} max={4000} step={100}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand"/>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">Quality (%)</label>
                  <div className="flex items-center gap-2">
                    <input type="range" min={60} max={100} value={imgQuality}
                      onChange={e => setImgQuality(+e.target.value)} className="flex-1 accent-brand"/>
                    <span className={`text-sm font-bold w-8 ${imgQuality >= 90 ? 'text-green-600' : imgQuality >= 80 ? 'text-yellow-600' : 'text-red-500'}`}>
                      {imgQuality}
                    </span>
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">EXIF Brand</label>
                  <input type="text" value={imgBrand} onChange={e => setImgBrand(e.target.value)}
                    placeholder="BreakTees"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand"/>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-gray-600">Rating EXIF</label>
                    <select value={imgRating} onChange={e => setImgRating(+e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand bg-white">
                      {[5,4,3,2,1].map(r => <option key={r} value={r}>{r} ⭐</option>)}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-gray-600">Ngày EXIF (-)</label>
                    <input type="number" value={imgDays} onChange={e => setImgDays(+e.target.value)}
                      min={0} max={365}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand"/>
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-100 pt-3 space-y-2">
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={imgRename} onChange={e => setImgRename(e.target.checked)} className="rounded accent-brand"/>
                  <span className="font-medium">Tự động rename file ảnh</span>
                </label>
                {imgRename && (
                  <div className="ml-6 space-y-1">
                    <label className="text-xs text-gray-600">Rename mode:</label>
                    <div className="space-y-1">
                      <label className="flex items-center gap-2 text-xs cursor-pointer">
                        <input type="radio" checked={imgRenameMode === 'classic'} onChange={() => setImgRenameMode('classic')} className="accent-brand"/>
                        <span><strong>Classic</strong> — "Black - T-Shirt.jpg" → "Design T-Shirt.jpg"</span>
                      </label>
                      <label className="flex items-center gap-2 text-xs cursor-pointer">
                        <input type="radio" checked={imgRenameMode === 'autodetect'} onChange={() => setImgRenameMode('autodetect')} className="accent-brand"/>
                        <span><strong>Auto-detect</strong> — "02.Black Gildan Mockup.jpg" → "Design Black T-Shirt.jpg"</span>
                      </label>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── Auto Pipeline Stepper ── */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-3">
            <Zap size={16} className="text-amber-500"/>
            <p className="text-sm font-semibold text-gray-800">Auto Pipeline</p>
            <span className="text-xs text-gray-400">— tắt browser sau khi submit, hệ thống tự chạy hết</span>
          </div>

          {/* Step 1 */}
          <PipelineStep step={1} icon="📤" title="Upload" desc="Upload file ZIP lên WooCommerce"
            enabled={true} disabled={false}>
          </PipelineStep>

          {/* Connector */}
          <div className="flex justify-center">
            <div className={`w-0.5 h-5 ${autoSeo ? 'bg-brand' : 'bg-gray-200'}`}/>
          </div>

          {/* Step 2 */}
          <PipelineStep step={2} icon="🤖" title="SEO" desc="Generate mô tả + Rank Math meta bằng AI"
            enabled={autoSeo} onToggle={handleToggleSeo} disabled={false}>
          </PipelineStep>

          {/* Connector */}
          <div className="flex justify-center">
            <div className={`w-0.5 h-5 ${autoPublish ? 'bg-brand' : 'bg-gray-200'}`}/>
          </div>

          {/* Step 3 */}
          <PipelineStep step={3} icon="🌐" title="Publish" desc="Publish tất cả SP sau khi SEO xong"
            enabled={autoPublish} onToggle={handleTogglePublish}
            disabled={!autoSeo} disabledReason="Cần bật SEO trước">
          </PipelineStep>

          {/* Connector */}
          <div className="flex justify-center">
            <div className={`w-0.5 h-5 ${autoReview ? 'bg-brand' : 'bg-gray-200'}`}/>
          </div>

          {/* Step 4 */}
          <PipelineStep step={4} icon="⭐" title="Fake Review" desc="Tự động tạo review + import vào WooCommerce"
            enabled={autoReview} onToggle={setAutoReview}
            disabled={!autoPublish} disabledReason="Cần bật Publish trước (SP phải Published mới review được)">

            {/* Review config */}
            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input type="checkbox" checked={useRange} onChange={e => setUseRange(e.target.checked)} className="rounded"/>
              Số review ngẫu nhiên theo khoảng
            </label>

            {useRange ? (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs text-gray-600">Min reviews</label>
                  <input type="number" value={countMin} onChange={e => setCountMin(+e.target.value)} min={1}
                    className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand bg-white"/>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-gray-600">Max reviews</label>
                  <input type="number" value={countMax} onChange={e => setCountMax(+e.target.value)} min={1}
                    className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand bg-white"/>
                </div>
              </div>
            ) : (
              <div className="space-y-1">
                <label className="text-xs text-gray-600">Số review mỗi SP</label>
                <input type="number" value={reviewCount} onChange={e => setReviewCount(+e.target.value)} min={1}
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand bg-white"/>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-gray-600">Ngày bắt đầu</label>
                <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand bg-white"/>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-gray-600">Ngày kết thúc</label>
                <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand bg-white"/>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-gray-600 font-medium">Phân bố rating</span>
                <span className={totalPct === 100 ? 'text-green-600 font-medium' : 'text-red-500 font-medium'}>
                  {totalPct}% {totalPct === 100 ? '✓' : '≠ 100%'}
                </span>
              </div>
              {[['5★', dist5, setDist5], ['4★', dist4, setDist4], ['3★', dist3, setDist3]].map(([label, val, setter]) => (
                <div key={label} className="flex items-center gap-3 text-xs">
                  <span className="w-6 font-medium">{label}</span>
                  <input type="range" min={0} max={100} value={val}
                    onChange={e => setter(+e.target.value)} className="flex-1 accent-brand"/>
                  <span className="w-8 text-right font-medium">{val}%</span>
                </div>
              ))}
            </div>

            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input type="checkbox" checked={skipReview} onChange={e => setSkipReview(e.target.checked)} className="rounded"/>
              Bỏ qua SP đã có review
            </label>

            {totalPct !== 100 && (
              <p className="text-xs text-red-500">⚠ Tổng phân bố rating phải = 100%</p>
            )}
          </PipelineStep>
        </div>

        <Button onClick={handleSubmit} disabled={!canSubmit} size="lg" className="w-full">
          {submitting ? <><Spinner size="sm"/> Đang thêm...</> : <><Upload size={16}/> Thêm vào hàng đợi</>}
        </Button>
      </Card>

      <JobQueuePanel/>
    </div>
  )
}
