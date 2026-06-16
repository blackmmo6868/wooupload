import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/client'
import { useAuthStore } from '../store/auth'
import { Button, Input } from '../components/shared/UI'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const navigate = useNavigate()
  const setAuth  = useAuthStore(s => s.setAuth)

  const handleLogin = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const data = await login(username, password)
      localStorage.setItem('token', data.access_token)
      setAuth({
        username: data.username,
        is_admin: data.is_admin,  // từ token response
      }, data.access_token)
      navigate('/upload')
    } catch (err) {
      setError(err.response?.data?.detail || 'Đăng nhập thất bại')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-blue-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-brand rounded-xl mb-4">
            <span className="text-white text-2xl font-bold">W</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">WooMMO Web</h1>
          <p className="text-sm text-gray-500 mt-1">Đăng nhập để tiếp tục</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <Input label="Tên đăng nhập" value={username}
            onChange={e => setUsername(e.target.value)} placeholder="admin" autoFocus required/>
          <Input label="Mật khẩu" type="password" value={password}
            onChange={e => setPassword(e.target.value)} placeholder="••••••••" required/>
          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{error}</div>
          )}
          <Button type="submit" className="w-full" size="lg" disabled={loading}>
            {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </Button>
        </form>
      </div>
    </div>
  )
}
