import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, Eye, EyeOff, Store } from 'lucide-react'
import api from '../../api/client'

const EMPTY = { name:'', wc_url:'', wp_username:'', wp_app_password:'', store_name:'', shortcode:'[thien_display_single_image]' }

function StoreForm({ form, setForm, onSave, onCancel, error, isEdit }) {
  const [showPass, setShowPass] = useState(false)
  const f = (k,v) => setForm(p => ({...p,[k]:v}))
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 mb-4 shadow-sm">
      <h3 className="font-semibold text-gray-800 mb-4">{isEdit ? 'Sửa Store' : 'Thêm Store mới'}</h3>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Tên store</label>
          <input className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={form.name} onChange={e=>f('name',e.target.value)} placeholder="BreakTees"/>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">WooCommerce URL</label>
          <input className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={form.wc_url} onChange={e=>f('wc_url',e.target.value)} placeholder="https://breaktees.com"/>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Store Name (dùng trong SEO)</label>
          <input className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={form.store_name} onChange={e=>f('store_name',e.target.value)} placeholder="BreakTees Store"/>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Custom Shortcode</label>
          <input className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={form.shortcode} onChange={e=>f('shortcode',e.target.value)} placeholder="[thien_display_single_image]"/>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">WordPress Username</label>
          <input className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={form.wp_username} onChange={e=>f('wp_username',e.target.value)} placeholder="admin"/>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">WP App Password {isEdit && <span className="text-gray-400">(trống = giữ nguyên)</span>}</label>
          <div className="relative">
            <input type={showPass?'text':'password'}
              className="w-full px-3 py-2 pr-9 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={form.wp_app_password} onChange={e=>f('wp_app_password',e.target.value)}
              placeholder={isEdit?"Nhập mới để đổi":"xxxx xxxx xxxx xxxx"}/>
            <button type="button" onClick={()=>setShowPass(!showPass)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              {showPass?<EyeOff size={14}/>:<Eye size={14}/>}
            </button>
          </div>
        </div>
      </div>
      {error && <p className="text-red-500 text-sm mt-3">{error}</p>}
      <div className="flex gap-2 mt-4">
        <button onClick={onSave} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
          {isEdit?'Lưu thay đổi':'Tạo Store'}
        </button>
        <button onClick={onCancel} className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">Hủy</button>
      </div>
    </div>
  )
}

export default function StoresPage() {
  const [stores,setStores]   = useState([])
  const [showAdd,setShowAdd] = useState(false)
  const [form,setForm]       = useState(EMPTY)
  const [editId,setEditId]   = useState(null)
  const [editForm,setEditForm] = useState(EMPTY)
  const [error,setError]     = useState('')
  const [editError,setEditError] = useState('')

  const load = async () => {
    try { const r = await api.get('/admin/stores'); setStores(r.data) } catch(e) {}
  }
  useEffect(()=>{load()},[])

  const handleCreate = async () => {
    setError('')
    if (!form.name||!form.wc_url){setError('Cần tên store và URL');return}
    try { await api.post('/admin/stores',form); setForm(EMPTY); setShowAdd(false); load() }
    catch(e){setError(e.response?.data?.detail||'Lỗi tạo store')}
  }

  const startEdit = (s) => {
    setEditId(s.id)
    setEditForm({name:s.name,wc_url:s.wc_url,wp_username:s.wp_username,wp_app_password:'',store_name:s.store_name,shortcode:s.shortcode})
    setEditError('')
  }

  const handleUpdate = async () => {
    setEditError('')
    try { await api.put(`/admin/stores/${editId}`,editForm); setEditId(null); load() }
    catch(e){setEditError(e.response?.data?.detail||'Lỗi cập nhật')}
  }

  const handleDelete = async (id,name,cnt) => {
    if(cnt>0){
      if(!confirm(`Store "${name}" đang có ${cnt} user được gán.\nXóa store sẽ bỏ gán tất cả user khỏi store này.\nBạn có chắc muốn xóa không?`))return
    } else {
      if(!confirm(`Xóa store "${name}"?`))return
    }
    try{await api.delete(`/admin/stores/${id}`);load()}
    catch(e){alert(e.response?.data?.detail||'Lỗi xóa')}
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Quản lý Store</h1>
          <p className="text-sm text-gray-500 mt-1">Mỗi store = 1 website WooCommerce</p>
        </div>
        <button onClick={()=>{setShowAdd(true);setError('')}}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
          <Plus size={16}/> Thêm Store
        </button>
      </div>

      {showAdd && <StoreForm form={form} setForm={setForm} onSave={handleCreate} onCancel={()=>setShowAdd(false)} error={error} isEdit={false}/>}

      <div className="space-y-3">
        {stores.length===0 && (
          <div className="text-center py-12 text-gray-400">
            <Store size={40} className="mx-auto mb-3 opacity-30"/>
            <p>Chưa có store nào. Thêm store đầu tiên!</p>
          </div>
        )}
        {stores.map(s=>(
          <div key={s.id}>
            {editId===s.id ? (
              <StoreForm form={editForm} setForm={setEditForm} onSave={handleUpdate} onCancel={()=>setEditId(null)} error={editError} isEdit={true}/>
            ):(
              <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <Store size={20} className="text-blue-600"/>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">{s.name}</span>
                    <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{s.user_count} user</span>
                    {s.has_wp_password && <span className="text-xs bg-green-50 text-green-600 px-2 py-0.5 rounded-full">✓ WP Pass</span>}
                  </div>
                  <p className="text-sm text-gray-500 truncate mt-0.5">{s.wc_url}</p>
                  <p className="text-xs text-gray-400 mt-0.5">SEO name: <span className="text-gray-600">{s.store_name||'—'}</span> · WP user: <span className="text-gray-600">{s.wp_username||'—'}</span></p>
                </div>
                <div className="flex gap-2">
                  <button onClick={()=>startEdit(s)} className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"><Edit2 size={16}/></button>
                  <button onClick={()=>handleDelete(s.id,s.name,s.user_count)} className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={16}/></button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
