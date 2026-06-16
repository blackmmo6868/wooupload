import { useState, useEffect } from 'react'
import { Plus, Check, Key, Store, Trash2, Eye, EyeOff } from 'lucide-react'
import { updateUser, deleteUser } from '../../api/client'
import api from '../../api/client'
import { Button, Card, Input, Badge } from '../../components/shared/UI'

const EMPTY_FORM = { username:'', email:'', password:'', is_admin:false, store_id:'', wp_username:'', wp_app_password:'' }

function PassInput({ value, onChange, placeholder }) {
  const [show, setShow] = useState(false)
  return (
    <div className="relative">
      <input type={show?'text':'password'} value={value} onChange={onChange} placeholder={placeholder}
        className="w-full px-3 py-2 pr-9 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"/>
      <button type="button" onClick={()=>setShow(!show)}
        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
        {show?<EyeOff size={14}/>:<Eye size={14}/>}
      </button>
    </div>
  )
}

function UserStoresPanel({ user, stores, onClose }) {
  const [userStores, setUserStores] = useState([])
  const [addForm, setAddForm]       = useState({ store_id:'', wp_username:'', wp_app_password:'' })
  const [showAdd, setShowAdd]       = useState(false)
  const [editId, setEditId]         = useState(null)
  const [editForm, setEditForm]     = useState({ wp_username:'', wp_app_password:'' })
  const [error, setError]           = useState('')

  const load = async () => {
    try {
      const r = await api.get(`/admin/users/${user.id}/stores`)
      setUserStores(r.data)
    } catch(e) {}
  }
  useEffect(() => { load() }, [])

  const availableStores = stores.filter(s => !userStores.find(us => us.store_id === s.id))

  const handleAdd = async () => {
    setError('')
    if (!addForm.store_id) { setError('Chọn store'); return }
    try {
      await api.post(`/admin/users/${user.id}/stores`, {
        store_id:        parseInt(addForm.store_id),
        wp_username:     addForm.wp_username,
        wp_app_password: addForm.wp_app_password,
      })
      setAddForm({ store_id:'', wp_username:'', wp_app_password:'' })
      setShowAdd(false); load()
    } catch(e) { setError(e.response?.data?.detail || 'Lỗi') }
  }

  const handleRemove = async (storeId) => {
    if (!confirm('Bỏ gán store này?')) return
    try { await api.delete(`/admin/users/${user.id}/stores/${storeId}`); load() }
    catch(e) { alert(e.response?.data?.detail || 'Lỗi') }
  }

  const handleEdit = async (storeId) => {
    try {
      await api.put(`/admin/users/${user.id}/stores/${storeId}`, {
        store_id:        storeId,
        wp_username:     editForm.wp_username,
        wp_app_password: editForm.wp_app_password,
      })
      setEditId(null); load()
    } catch(e) { alert(e.response?.data?.detail || 'Lỗi') }
  }

  return (
    <tr className="bg-blue-50">
      <td colSpan={8} className="px-4 py-4">
        <div className="max-w-3xl">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-gray-800">Stores của <span className="text-blue-600">{user.username}</span></h4>
            <div className="flex gap-2">
              <Button size="sm" onClick={() => setShowAdd(!showAdd)}><Plus size={12}/> Thêm Store</Button>
              <Button size="sm" variant="outline" onClick={onClose}>Đóng</Button>
            </div>
          </div>

          {showAdd && (
            <div className="bg-white border border-gray-200 rounded-lg p-3 mb-3">
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">Store</label>
                  <select value={addForm.store_id} onChange={e=>setAddForm({...addForm,store_id:e.target.value})}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500">
                    <option value="">-- Chọn store --</option>
                    {availableStores.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">WP Username</label>
                  <input value={addForm.wp_username} onChange={e=>setAddForm({...addForm,wp_username:e.target.value})}
                    placeholder="WP login name"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"/>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">WP App Password</label>
                  <PassInput value={addForm.wp_app_password}
                    onChange={e=>setAddForm({...addForm,wp_app_password:e.target.value})}
                    placeholder="xxxx xxxx xxxx xxxx"/>
                </div>
              </div>
              {error && <p className="text-red-500 text-xs mt-2">{error}</p>}
              <div className="flex gap-2 mt-3">
                <Button size="sm" onClick={handleAdd}><Check size={12}/> Thêm</Button>
                <Button size="sm" variant="outline" onClick={()=>setShowAdd(false)}>Hủy</Button>
              </div>
            </div>
          )}

          {userStores.length === 0 ? (
            <p className="text-gray-400 text-sm">Chưa gán store nào. Bấm "Thêm Store" để gán.</p>
          ) : (
            <div className="space-y-2">
              {userStores.map(us => (
                <div key={us.id} className="bg-white border border-gray-200 rounded-lg px-3 py-2 flex items-center gap-4">
                  <div className="flex-1">
                    <span className="font-medium text-gray-900 text-sm">{us.store_name}</span>
                    <span className="text-gray-400 text-xs ml-2">{us.store_url}</span>
                  </div>
                  <div className="text-xs text-gray-500 flex-1">
                    WP: <span className="font-medium text-gray-700">{us.wp_username || <span className="text-gray-300">dùng của store</span>}</span>
                    {us.has_wp_password && <span className="text-green-500 ml-1">✓ pass</span>}
                  </div>
                  {editId === us.store_id ? (
                    <div className="flex items-center gap-2">
                      <input value={editForm.wp_username} onChange={e=>setEditForm({...editForm,wp_username:e.target.value})}
                        placeholder="WP Username" className="px-2 py-1 text-xs border border-gray-300 rounded w-28 focus:outline-none focus:border-blue-500"/>
                      <PassInput value={editForm.wp_app_password} onChange={e=>setEditForm({...editForm,wp_app_password:e.target.value})} placeholder="New password"/>
                      <button onClick={()=>handleEdit(us.store_id)} className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700">Lưu</button>
                      <button onClick={()=>setEditId(null)} className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">Hủy</button>
                    </div>
                  ) : (
                    <button onClick={()=>{ setEditId(us.store_id); setEditForm({wp_username:us.wp_username||'',wp_app_password:''}) }}
                      className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 text-gray-600">Sửa</button>
                  )}
                  <button onClick={()=>handleRemove(us.store_id)}
                    className="p-1 text-gray-400 hover:text-red-500 rounded">
                    <Trash2 size={14}/>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </td>
    </tr>
  )
}

export default function AdminUsersPage() {
  const [users,setUsers]     = useState([])
  const [stores,setStores]   = useState([])
  const [showAdd,setShowAdd] = useState(false)
  const [form,setForm]       = useState(EMPTY_FORM)
  const [expandedUser,setExpandedUser] = useState(null)
  const [error,setError]     = useState('')
  const [passModal,setPassModal]     = useState(null)
  const [editModal,setEditModal]     = useState(null)
  const [editUserForm,setEditUserForm] = useState({})
  const [newPass,setNewPass]         = useState('')
  const [passErr,setPassErr]         = useState('')
  const [passLoading,setPassLoading] = useState(false)

  const load = async () => {
    try {
      const [u,s] = await Promise.all([
        api.get('/admin/users').then(r=>r.data),
        api.get('/admin/stores').then(r=>r.data),
      ])
      setUsers(u); setStores(s)
    } catch(e) {}
  }
  useEffect(()=>{load()},[])

  const handleCreate = async () => {
    setError('')
    if(!form.username||!form.password){setError('Cần username và password');return}
    try {
      const res = await api.post('/admin/users',{
        username: form.username, email: form.email, password: form.password,
        is_admin: form.is_admin, store_id: null,
      })
      // Nếu chọn store, tự động gán vào user_stores
      if (form.store_id && res.data.id) {
        await api.post(`/admin/users/${res.data.id}/stores`, {
          store_id:        parseInt(form.store_id),
          wp_username:     form.wp_username,
          wp_app_password: form.wp_app_password,
        })
      }
      setForm(EMPTY_FORM); setShowAdd(false); load()
    } catch(e){setError(e.response?.data?.detail||'Lỗi tạo user')}
  }

  const handleDelete = async (id) => {
    if(!confirm('Xóa user này?'))return
    try{await deleteUser(id);load()}catch(e){}
  }

  const handleToggleActive = async (u) => {
    try{await updateUser(u.id,{is_active:!u.is_active});load()}catch(e){}
  }

  const handleSaveEditUser = async () => {
    try {
      await api.put(`/admin/users/${editModal.id}`, editUserForm)
      setEditModal(null); load()
    } catch(e) { alert(e.response?.data?.detail || 'Lỗi') }
  }

  const handleChangePass = async () => {
    if(!newPass||newPass.length<6){setPassErr('Tối thiểu 6 ký tự');return}
    setPassLoading(true); setPassErr('')
    try {
      await api.post(`/admin/users/${passModal.id}/change-password`,{new_password:newPass})
      setPassModal(null); setNewPass(''); alert('✅ Đã đổi mật khẩu cho '+passModal.username)
    } catch(e){setPassErr(e.response?.data?.detail||'Lỗi')}
    finally{setPassLoading(false)}
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý User</h1>
          <p className="text-sm text-gray-500 mt-1">Mỗi user có thể gán nhiều store với WP credentials riêng</p>
        </div>
        <Button onClick={()=>setShowAdd(!showAdd)}><Plus size={16}/> Thêm User</Button>
      </div>

      {showAdd && (
        <Card className="p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">Tạo tài khoản mới</h2>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Username" value={form.username}
              onChange={e=>setForm({...form,username:e.target.value})} placeholder="vd: vuvp"/>
            <Input label="Email" value={form.email}
              onChange={e=>setForm({...form,email:e.target.value})} placeholder="email@example.com"/>
            <Input label="Password WooMMO" type="password" value={form.password}
              onChange={e=>setForm({...form,password:e.target.value})} placeholder="≥ 8 ký tự"/>
            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">Store đầu tiên <span className="text-gray-400 font-normal">(tùy chọn)</span></label>
              <select value={form.store_id} onChange={e=>setForm({...form,store_id:e.target.value})}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500">
                <option value="">-- Chọn store --</option>
                {stores.map(s=><option key={s.id} value={s.id}>{s.name} ({s.wc_url})</option>)}
              </select>
            </div>
            {form.store_id && <>
              <div className="space-y-1">
                <label className="block text-sm font-medium text-gray-700">WP Username <span className="text-gray-400 font-normal">(cho store trên)</span></label>
                <Input value={form.wp_username} onChange={e=>setForm({...form,wp_username:e.target.value})} placeholder="WP login name"/>
              </div>
              <div className="space-y-1">
                <label className="block text-sm font-medium text-gray-700">WP App Password</label>
                <PassInput value={form.wp_app_password} onChange={e=>setForm({...form,wp_app_password:e.target.value})} placeholder="xxxx xxxx xxxx xxxx"/>
              </div>
            </>}
          </div>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={form.is_admin} onChange={e=>setForm({...form,is_admin:e.target.checked})} className="rounded"/>
            Cấp quyền Admin
          </label>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-3">
            <Button onClick={handleCreate}>Tạo tài khoản</Button>
            <Button variant="outline" onClick={()=>{setShowAdd(false);setError('')}}>Hủy</Button>
          </div>
        </Card>
      )}

      <Card className="overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {['#','Username','Email','Quyền','Trạng thái','Hành động'].map(h=>(
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {users.map((u,idx)=>(
              <>
                <tr key={u.id} className={`hover:bg-gray-50 ${expandedUser===u.id?'bg-blue-50':''}`}>
                  <td className="px-4 py-3 text-gray-400">#{idx+1}</td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-900">{u.username}</p>
                    {u.note && <p className="text-xs text-gray-400 truncate max-w-[120px]" title={u.note}>{u.note}</p>}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{u.email}</td>
                  <td className="px-4 py-3"><Badge variant={u.is_admin?'warning':'default'}>{u.is_admin?'Admin':'Member'}</Badge></td>
                  <td className="px-4 py-3"><Badge variant={u.is_active?'success':'default'}>{u.is_active?'Active':'Disabled'}</Badge></td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      <Button size="sm" variant="outline"
                        onClick={()=>{ setEditModal(u); setEditUserForm({username:u.username,email:u.email,note:u.note||''}) }}>
                        ✏️ Sửa
                      </Button>
                      <Button size="sm" variant={expandedUser===u.id?'primary':'outline'}
                        onClick={()=>setExpandedUser(expandedUser===u.id?null:u.id)}>
                        <Store size={12}/> Stores
                      </Button>
                      <Button size="sm" variant="outline"
                        onClick={()=>{setPassModal({id:u.id,username:u.username});setNewPass('');setPassErr('')}}>
                        <Key size={12}/> Pass
                      </Button>
                      <Button size="sm" variant="outline" onClick={()=>handleToggleActive(u)}>
                        {u.is_active?'Disable':'Enable'}
                      </Button>
                      <Button size="sm" variant="danger" onClick={()=>handleDelete(u.id)}>Xóa</Button>
                    </div>
                  </td>
                </tr>
                {expandedUser===u.id && (
                  <UserStoresPanel key={`panel-${u.id}`} user={u} stores={stores}
                    onClose={()=>setExpandedUser(null)}/>
                )}
              </>
            ))}
          </tbody>
        </table>
      </Card>

      {editModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={()=>setEditModal(null)}>
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md space-y-4" onClick={e=>e.stopPropagation()}>
            <h3 className="font-semibold text-gray-900">✏️ Chỉnh sửa User</h3>
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-sm font-medium text-gray-700">Username</label>
                <Input value={editUserForm.username||''} onChange={e=>setEditUserForm({...editUserForm,username:e.target.value})} placeholder="username"/>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-gray-700">Email</label>
                <Input value={editUserForm.email||''} onChange={e=>setEditUserForm({...editUserForm,email:e.target.value})} placeholder="email@example.com"/>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-gray-700">Note <span className="text-gray-400 font-normal">(ghi chú nội bộ)</span></label>
                <textarea value={editUserForm.note||''} onChange={e=>setEditUserForm({...editUserForm,note:e.target.value})}
                  placeholder="VD: quản lý store shoes, liên hệ qua Zalo..."
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 h-20 resize-none"/>
              </div>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={()=>setEditModal(null)}>Hủy</Button>
              <Button className="flex-1" onClick={handleSaveEditUser}>Lưu</Button>
            </div>
          </div>
        </div>
      )}

      {passModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={()=>setPassModal(null)}>
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm space-y-4" onClick={e=>e.stopPropagation()}>
            <h3 className="font-semibold text-gray-900">🔑 Đổi mật khẩu WooMMO</h3>
            <p className="text-sm text-gray-500">User: <strong>{passModal.username}</strong></p>
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700">Mật khẩu mới</label>
              <Input type="password" value={newPass} onChange={e=>setNewPass(e.target.value)}
                placeholder="Tối thiểu 6 ký tự" onKeyDown={e=>e.key==='Enter'&&handleChangePass()}/>
              {passErr && <p className="text-xs text-red-500">{passErr}</p>}
            </div>
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={()=>setPassModal(null)}>Hủy</Button>
              <Button className="flex-1" onClick={handleChangePass} disabled={passLoading}>
                {passLoading?'Đang lưu...':'Xác nhận'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
