import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Instance riêng cho upload — timeout dài hơn
const uploadApi = axios.create({
  baseURL: '/api',
  timeout: 600000, // 10 phút
})
uploadApi.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// ── Auth ───────────────────────────────────────────────────────────────────────
export const login = async (username, password) => {
  const form = new URLSearchParams({ username, password })
  const { data } = await api.post('/auth/token', form)
  return data
}
export const getMe = () => api.get('/auth/me').then(r => r.data)
export const changePassword = (old_password, new_password) =>
  api.post('/auth/change-password', { old_password, new_password }).then(r => r.data)

// ── Products ───────────────────────────────────────────────────────────────────
export const getProducts = (params) => api.get('/products/', { params }).then(r => r.data)
export const getProductsByStore = (params, store_id) => api.get('/products/', { params: {...params, store_id} }).then(r => r.data)
export const getCategories = () => api.get('/products/categories').then(r => r.data)
export const getReviewCounts = (ids, store_id=0) =>
  api.get('/products/review-counts', { params: { ids: ids.join(','), store_id } }).then(r => r.data)
export const getWcpaForms = () => api.get('/products/wcpa-forms').then(r => r.data)
export const getBrands = () => api.get('/products/brands').then(r => r.data)

// ── Jobs ───────────────────────────────────────────────────────────────────────
export const startUpload = (formData, onProgress) => uploadApi.post('/jobs/upload', formData, {
  onUploadProgress: e => {
    if (onProgress && e.total) {
      onProgress(Math.round((e.loaded * 100) / e.total))
    }
  }
}).then(r => r.data)
export const startSeo = (payload) => api.post('/jobs/seo', payload).then(r => r.data)
export const startSeoStore = (payload, store_id) => {
  const fd = new FormData()
  Object.entries({...payload, store_id}).forEach(([k,v]) => {
    fd.append(k, Array.isArray(v) ? JSON.stringify(v) : v)
  })
  return api.post('/jobs/seo', fd).then(r => r.data)
}
export const startReview = (payload) => api.post('/jobs/review', payload).then(r => r.data)
export const startReviewStore = (payload, store_id) => {
  const fd = new FormData()
  Object.entries({...payload, store_id}).forEach(([k,v]) => {
    fd.append(k, Array.isArray(v) ? JSON.stringify(v) : v)
  })
  return api.post('/jobs/review', fd).then(r => r.data)
}
export const getJobStatus = (id) => api.get(`/jobs/${id}/status`).then(r => r.data)
export const getJobLog = (id) => api.get(`/jobs/${id}/log`).then(r => r.data)
export const listJobs = (params) => api.get('/jobs/', { params }).then(r => r.data)

// ── Admin ──────────────────────────────────────────────────────────────────────
export const listUsers = () => api.get('/admin/users').then(r => r.data)
export const createUser = (data) => api.post('/admin/users', data).then(r => r.data)
export const updateUser = (id, data) => api.put(`/admin/users/${id}`, data).then(r => r.data)
export const deleteUser = (id) => api.delete(`/admin/users/${id}`).then(r => r.data)
export const getSettings = () => api.get('/admin/settings').then(r => r.data)
export const updateSettings = (data) => api.post('/admin/settings', data).then(r => r.data)

// ── Category cache (RAM, TTL 5 phút) ──────────────────────────────────────────
const _catCache = {}
export const getCategoriesCached = async (storeId) => {
  const key = `cat_${storeId}`
  const now = Date.now()
  if (_catCache[key] && (now - _catCache[key].ts) < 5 * 60 * 1000) {
    return _catCache[key].data
  }
  const r = await api.get(`/products/categories?store_id=${storeId}`)
  const data = Array.isArray(r.data) ? r.data : []
  _catCache[key] = { data, ts: now }
  return data
}

const _wcpaCache = {}
export const getWcpaFormsCached = async (storeId) => {
  const key = `wcpa_${storeId}`
  const now = Date.now()
  if (_wcpaCache[key] && (now - _wcpaCache[key].ts) < 5 * 60 * 1000)
    return _wcpaCache[key].data
  const r = await api.get(`/products/wcpa-forms?store_id=${storeId}`)
  const data = Array.isArray(r.data) ? r.data : []
  _wcpaCache[key] = { data, ts: now }
  return data
}

const _brandCache = {}
export const getBrandsCached = async (storeId) => {
  const key = `brand_${storeId}`
  const now = Date.now()
  if (_brandCache[key] && (now - _brandCache[key].ts) < 5 * 60 * 1000)
    return _brandCache[key].data
  const r = await api.get(`/products/brands?store_id=${storeId}`)
  const data = Array.isArray(r.data) ? r.data : []
  _brandCache[key] = { data, ts: now }
  return data
}
