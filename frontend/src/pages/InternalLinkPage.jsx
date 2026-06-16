import { useState, useEffect } from 'react'
import { Save, Plus, Trash2, Search } from 'lucide-react'
import { getCategories, getProducts } from '../api/client'
import { useAuthStore } from '../store/auth'
import { Button, Card, Spinner } from '../components/shared/UI'
import api from '../api/client'

const saveConfig = (data, storeId) => api.post(`/links/config?store_id=${storeId||0}`, data).then(r => r.data)
const loadConfig = (storeId) => api.get(`/links/config?store_id=${storeId||0}`).then(r => r.data)

export default function InternalLinkPage() {
  const { selectedStore } = useAuthStore()
  const [linkMode, setLinkMode]           = useState('category')
  const [catLinks, setCatLinks]           = useState([])
  const [productPool, setProductPool]     = useState([])
  const [allCategories, setAllCategories] = useState([])
  const [loadingCats, setLoadingCats]     = useState(false)
  const [prodSearch, setProdSearch]       = useState('')
  const [prodResults, setProdResults]     = useState([])
  const [searching, setSearching]         = useState(false)
  const [saved, setSaved]                 = useState(false)
  const [saving, setSaving]               = useState(false)

  useEffect(() => {
    loadConfig(selectedStore?.id).then(data => {
      if (data.mode)                   setLinkMode(data.mode)
      if (data.category_links?.length) setCatLinks(data.category_links)
      if (data.product_pool?.length)   setProductPool(data.product_pool)
    }).catch(() => {})
  }, [])

  // ── Category ──────────────────────────────────────────────────────────────
  const loadCategories = async () => {
    setLoadingCats(true)
    try {
      const cats = await (selectedStore?.id ? api.get(`/products/categories?store_id=${selectedStore.id}`).then(r=>r.data) : getCategories())
      setAllCategories(cats)
    } catch(e) { alert('Lỗi: ' + e.message) }
    finally { setLoadingCats(false) }
  }

  const addCategory      = (cat) => {
    if (catLinks.find(c => c.name === cat.name)) return
    setCatLinks(prev => [...prev, { name: cat.name, url: cat.url }])
  }
  const selectAllCats    = () => setCatLinks(allCategories.map(c => ({ name: c.name, url: c.url })))
  const clearAllCats     = () => setCatLinks([])
  const removeCat        = (i)       => setCatLinks(prev => prev.filter((_, idx) => idx !== i))
  const updateCatUrl     = (i, url)  => setCatLinks(prev => prev.map((item, idx) => idx === i ? {...item, url}  : item))
  const updateCatName    = (i, name) => setCatLinks(prev => prev.map((item, idx) => idx === i ? {...item, name} : item))

  // ── Product ───────────────────────────────────────────────────────────────
  const searchProducts = async () => {
    if (!prodSearch.trim()) return
    setSearching(true)
    try {
      let all = [], page = 1
      while (all.length < 100) {
        const data = await getProducts({ search: prodSearch, per_page: 50, page, store_id: selectedStore?.id || 0 })
        all = [...all, ...(data.products || [])]
        if (page >= (data.total_pages || 1) || all.length >= 100) break
        page++
      }
      setProdResults(all.slice(0, 100))
    } catch(e) {}
    finally { setSearching(false) }
  }

  const addToPool        = (p) => {
    if (productPool.find(x => x.title === p.name)) return
    setProductPool(prev => [...prev, { title: p.name, url: p.url || '' }])
  }
  const selectAllResults = () => prodResults.forEach(p => {
    if (!productPool.find(x => x.title === p.name))
      setProductPool(prev => [...prev, { title: p.name, url: p.url || '' }])
  })
  const removeFromPool   = (i)      => setProductPool(prev => prev.filter((_, idx) => idx !== i))
  const updatePoolUrl    = (i, url) => setProductPool(prev => prev.map((item, idx) => idx === i ? {...item, url} : item))

  // ── Save ──────────────────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaving(true)
    try {
      await saveConfig({
        mode:           linkMode,
        category_links: catLinks.filter(c => c.name && c.url),
        product_pool:   productPool.filter(p => p.title && p.url),
      }, selectedStore?.id)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch(e) { alert('Lỗi lưu: ' + e.message) }
    finally { setSaving(false) }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Internal Link</h1>
        <p className="text-sm text-gray-500 mt-1">Cấu hình link nội bộ tự động chèn vào mô tả khi generate SEO</p>
      </div>

      <Card className="p-6 space-y-5">
        {/* Mode */}
        <div className="flex gap-8">
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="radio" checked={linkMode === 'category'} onChange={() => setLinkMode('category')} className="accent-brand w-4 h-4"/>
            <div>
              <p className="text-sm font-medium text-gray-900">Category mode</p>
              <p className="text-xs text-gray-400">AI tự match niche → link đúng danh mục</p>
            </div>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="radio" checked={linkMode === 'product'} onChange={() => setLinkMode('product')} className="accent-brand w-4 h-4"/>
            <div>
              <p className="text-sm font-medium text-gray-900">Product mode</p>
              <p className="text-xs text-gray-400">Round-robin qua pool sản phẩm</p>
            </div>
          </label>
        </div>

        <div className="border-t border-gray-100 pt-4">

          {/* ── CATEGORY MODE ── */}
          {linkMode === 'category' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 flex-wrap">
                <Button variant="outline" size="sm" onClick={loadCategories} disabled={loadingCats}>
                  {loadingCats && <Spinner size="sm"/>} Load danh mục
                </Button>
                {allCategories.length > 0 && (
                  <>
                    <Button size="sm" onClick={selectAllCats}>Chọn tất cả ({allCategories.length})</Button>
                    <Button variant="outline" size="sm" onClick={clearAllCats}>Bỏ chọn tất cả</Button>
                  </>
                )}
              </div>

              {allCategories.length > 0 && (
                <div className="border border-gray-200 rounded-lg p-3 max-h-52 overflow-y-auto">
                  <p className="text-xs text-gray-400 mb-2">Click để thêm/bỏ:</p>
                  <div className="flex flex-wrap gap-2">
                    {allCategories.map(cat => {
                      const added = catLinks.find(c => c.name === cat.name)
                      return (
                        <button key={cat.id}
                          onClick={() => added ? removeCat(catLinks.findIndex(c => c.name === cat.name)) : addCategory(cat)}
                          title={cat.url}
                          className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                            added ? 'bg-brand text-white border-brand' : 'border-gray-300 text-gray-700 hover:border-brand hover:text-brand'
                          }`}>
                          {cat.name} {cat.count > 0 ? `(${cat.count})` : ''} {added ? '✓' : ''}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}

              {catLinks.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{catLinks.length} danh mục — URL thật từ WooCommerce:</p>
                  <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
                    {catLinks.map((item, i) => (
                      <div key={i} className="flex gap-2 items-center">
                        <input value={item.name} onChange={e => updateCatName(i, e.target.value)}
                          className="w-40 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand flex-shrink-0"/>
                        <input value={item.url} onChange={e => updateCatUrl(i, e.target.value)}
                          placeholder="URL category"
                          className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand"/>
                        <button onClick={() => removeCat(i)} className="text-red-400 hover:text-red-600 p-1.5 flex-shrink-0">
                          <Trash2 size={15}/>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-400 text-sm border-2 border-dashed border-gray-200 rounded-lg">
                  Bấm "Load danh mục" rồi "Chọn tất cả" hoặc click từng danh mục
                </div>
              )}

              <button onClick={() => setCatLinks(prev => [...prev, { name: '', url: '' }])}
                className="flex items-center gap-1 text-sm text-brand font-medium hover:underline">
                <Plus size={14}/> Thêm thủ công
              </button>
            </div>
          )}

          {/* ── PRODUCT MODE ── */}
          {linkMode === 'product' && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">Tìm sản phẩm → thêm vào pool → SEO round-robin link đến từng sản phẩm (tối đa 100 kết quả)</p>

              <div className="flex gap-2">
                <input value={prodSearch} onChange={e => setProdSearch(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && searchProducts()}
                  placeholder="Nhập tên sản phẩm để tìm..."
                  className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand"/>
                <Button variant="outline" onClick={searchProducts} disabled={searching}>
                  {searching ? <Spinner size="sm"/> : <Search size={14}/>} Tìm
                </Button>
              </div>

              {prodResults.length > 0 && (
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border-b border-gray-200">
                    <span className="text-xs text-gray-500">{prodResults.length} kết quả</span>
                    <Button size="sm" onClick={selectAllResults}>Thêm tất cả ({prodResults.length})</Button>
                  </div>
                  <div className="divide-y divide-gray-100 max-h-64 overflow-y-auto">
                    {prodResults.map(p => {
                      const inPool = productPool.find(x => x.title === p.name)
                      return (
                        <div key={p.id} className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50">
                          {p.image && <img src={p.image} alt="" className="w-8 h-8 rounded object-cover flex-shrink-0"/>}
                          <span className="flex-1 text-sm truncate text-gray-800">{p.name}</span>
                          <button onClick={() => !inPool && addToPool(p)}
                            className={`text-xs px-3 py-1 rounded-full border flex-shrink-0 transition-colors ${
                              inPool ? 'bg-brand text-white border-brand cursor-default' : 'border-gray-300 hover:border-brand hover:text-brand'
                            }`}>
                            {inPool ? '✓ Đã thêm' : '+ Thêm'}
                          </button>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {productPool.length > 0 ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Pool ({productPool.length} SP) — round-robin:</p>
                    <button onClick={() => setProductPool([])} className="text-xs text-red-400 hover:text-red-600">Xóa tất cả</button>
                  </div>
                  <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
                    {productPool.map((item, i) => (
                      <div key={i} className="flex gap-2 items-center">
                        <span className="text-xs text-gray-400 w-6 text-center flex-shrink-0">{i+1}</span>
                        <span className="w-44 text-sm text-gray-700 truncate flex-shrink-0" title={item.title}>{item.title}</span>
                        <input value={item.url} onChange={e => updatePoolUrl(i, e.target.value)}
                          placeholder="URL sản phẩm"
                          className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand"/>
                        <button onClick={() => removeFromPool(i)} className="text-red-400 hover:text-red-600 p-1.5 flex-shrink-0">
                          <Trash2 size={15}/>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-400 text-sm border-2 border-dashed border-gray-200 rounded-lg">
                  Tìm sản phẩm và thêm vào pool bên trên
                </div>
              )}
            </div>
          )}

        </div>
      </Card>

      <Button onClick={handleSave} disabled={saving} size="lg">
        <Save size={16}/>
        {saving ? 'Đang lưu...' : saved ? '✅ Đã lưu!' : 'Lưu cấu hình'}
      </Button>
    </div>
  )
}
