import { useState, useEffect } from 'react'
import { Save, Eye, EyeOff, Plus, Trash2, Search } from 'lucide-react'
import { getSettings, updateSettings, getCategories, getProducts } from '../../api/client'
import { Button, Card, Input, Spinner } from '../../components/shared/UI'

function SecretInput({ label, value, onChange, hint, isSaved }) {
  const [show, setShow]     = useState(false)
  const [editing, setEditing] = useState(false)

  // Nếu key đã lưu và user chưa bấm sửa → hiển thị ***
  const displayValue = (isSaved && !editing) ? '' : value

  const handleChange = (e) => {
    setEditing(true)
    onChange(e)
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <label className="block text-sm font-medium text-gray-700">{label}</label>
        {isSaved && (
          <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full border border-green-200">
            ✓ Da luu
          </span>
        )}
      </div>
      <div className="relative">
        <input
          type={show ? 'text' : 'password'}
          value={displayValue}
          onChange={handleChange}
          onFocus={() => isSaved && setEditing(true)}
          placeholder={isSaved && !editing ? '••••••••••••••••••••' : (hint || '')}
          className={`w-full px-3 py-2 pr-20 text-sm border rounded-lg focus:outline-none focus:border-brand ${
            isSaved && !editing ? 'border-green-300 bg-green-50' : 'border-gray-300'
          }`}
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isSaved && !editing && (
            <button type="button" onClick={() => setEditing(true)}
              className="text-xs text-brand hover:underline px-1">
              Sua
            </button>
          )}
          {editing && (
            <button type="button" onClick={() => { setEditing(false); onChange({ target: { value: '' } }) }}
              className="text-xs text-gray-400 hover:text-gray-600 px-1">
              Huy
            </button>
          )}
          <button type="button" onClick={() => setShow(!show)}
            className="text-gray-400 hover:text-gray-600">
            {show ? <EyeOff size={16}/> : <Eye size={16}/>}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function AdminSettingsPage() {
  const [settings, setSettings]   = useState({})
  const [savedKeys, setSavedKeys] = useState({})
  const [saved, setSaved]         = useState(false)
  const [saving, setSaving]       = useState(false)

  const [linkMode, setLinkMode]       = useState('category')
  const [catLinks, setCatLinks]       = useState([])
  const [productPool, setProductPool] = useState([])
  const [allCategories, setAllCategories] = useState([])
  const [loadingCats, setLoadingCats] = useState(false)
  const [prodSearch, setProdSearch]   = useState('')
  const [prodResults, setProdResults] = useState([])
  const [searchingProd, setSearchingProd] = useState(false)

  useEffect(() => {
    getSettings().then(data => {
      const s = { ...data }
      const sk = {}
      for (const k of ['openai_key', 'serper_key', 'gemini_key']) {
        sk[k] = !!(s[k] && s[k].includes('*'))
        if (s[k] && s[k].startsWith('*')) s[k] = ''
      }
      setSavedKeys(sk)
      setSettings(s)
      try {
        const lc = JSON.parse(s.link_config || '{}')
        if (lc.mode) setLinkMode(lc.mode)
        if (lc.category_links?.length) setCatLinks(lc.category_links)
        if (lc.product_pool?.length)   setProductPool(lc.product_pool)
      } catch(e) {}
    })
  }, [])

  const set = (k, v) => setSettings(prev => ({ ...prev, [k]: v }))

  const loadCategories = async () => {
    setLoadingCats(true)
    try { setAllCategories(await getCategories()) }
    catch(e) { alert('Loi: ' + e.message) }
    finally { setLoadingCats(false) }
  }

  const addCategory      = (cat) => {
    if (!catLinks.find(c => c.name === cat.name))
      setCatLinks(prev => [...prev, { name: cat.name, url: cat.url }])
  }
  const selectAllCats    = () => setCatLinks(allCategories.map(c => ({ name: c.name, url: c.url })))
  const clearAllCats     = () => setCatLinks([])
  const removeCat        = (i)     => setCatLinks(prev => prev.filter((_, x) => x !== i))
  const updateCatUrl     = (i, v)  => setCatLinks(prev => prev.map((it, x) => x === i ? {...it, url: v}  : it))
  const updateCatName    = (i, v)  => setCatLinks(prev => prev.map((it, x) => x === i ? {...it, name: v} : it))

  const searchProducts = async () => {
    if (!prodSearch.trim()) return
    setSearchingProd(true)
    try {
      const data = await getProducts({ search: prodSearch, per_page: 20 })
      setProdResults(data.products || [])
    } catch(e) {}
    finally { setSearchingProd(false) }
  }

  const addToPool      = (p) => {
    if (!productPool.find(x => x.title === p.name))
      setProductPool(prev => [...prev, { title: p.name, url: p.url || '' }])
  }
  const removeFromPool = (i)    => setProductPool(prev => prev.filter((_, x) => x !== i))
  const updatePoolUrl  = (i, v) => setProductPool(prev => prev.map((it, x) => x === i ? {...it, url: v} : it))

  const buildLinkConfig = () => JSON.stringify(
    linkMode === 'category'
      ? { mode: 'category', category_links: catLinks.filter(c => c.name && c.url) }
      : { mode: 'product',  product_pool:   productPool.filter(p => p.title && p.url) }
  )

  const handleSave = async () => {
    setSaving(true)
    try {
      const SECRET_KEYS = ['openai_key', 'serper_key', 'gemini_key']
      const payload = {}
      for (const [k, v] of Object.entries(settings)) {
        if (v === '' || v === undefined || v === null) continue
        if (SECRET_KEYS.includes(k) && (!v || v.includes('*'))) continue
        payload[k] = v
      }
      payload.link_config = buildLinkConfig()
      await updateSettings(payload)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      alert('Loi: ' + (e.response?.data?.detail || e.message))
    } finally { setSaving(false) }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cai dat</h1>
        <p className="text-sm text-gray-500">Cau hinh API keys va tuy chon chung</p>
      </div>

      <Card className="p-6 space-y-5">
        <h2 className="font-semibold text-gray-900">API Keys</h2>
        <SecretInput label="OpenAI API Key" value={settings.openai_key || ''}
          onChange={e => set('openai_key', e.target.value)} hint="sk-..."
          isSaved={savedKeys.openai_key}/>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">OpenAI Model</label>
          <select value={settings.openai_model || 'gpt-4o'}
            onChange={e => set('openai_model', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-brand bg-white">
            <option value="gpt-4o">gpt-4o (khuyen dung)</option>
            <option value="gpt-4o-mini">gpt-4o-mini (tiet kiem hon)</option>
          </select>
        </div>
        <SecretInput label="Serper API Key" value={settings.serper_key || ''}
          onChange={e => set('serper_key', e.target.value)} hint="De trong neu khong dung"
          isSaved={savedKeys.serper_key}/>
        <SecretInput label="Gemini API Key" value={settings.gemini_key || ''}
          onChange={e => set('gemini_key', e.target.value)} hint="De trong neu khong dung"
          isSaved={savedKeys.gemini_key}/>
      </Card>


      <Button onClick={handleSave} disabled={saving} size="lg">
        <Save size={16}/>
        {saving ? 'Dang luu...' : saved ? '✅ Da luu!' : 'Luu cai dat'}
      </Button>
    </div>
  )
}
