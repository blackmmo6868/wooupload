import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuthStore } from './store/auth'
import { getMe } from './api/client'

import Layout            from './components/shared/Layout'
import LoginPage         from './pages/LoginPage'
import UploadPage        from './pages/UploadPage'
import SEOPage           from './pages/SEOPage'
import ReviewPage        from './pages/ReviewPage'
import InternalLinkPage  from './pages/InternalLinkPage'
import ExportLinksPage   from './pages/ExportLinksPage'
import SubmitIndexPage   from './pages/SubmitIndexPage'
import AdminUsersPage    from './pages/admin/UsersPage'
import AdminSettingsPage from './pages/admin/SettingsPage'
import JobManagerPage    from './pages/admin/JobManagerPage'
import StoresPage        from './pages/admin/StoresPage'

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, token } = useAuthStore()
  if (!token) return <Navigate to="/login" replace />
  if (adminOnly && !user?.is_admin) return <Navigate to="/" replace />
  return <Layout>{children}</Layout>
}

export default function App() {
  const { token, setAuth, logout } = useAuthStore()
  const [loading, setLoading]      = useState(true)

  useEffect(() => {
    if (!token) { setLoading(false); return }
    getMe().then(me => setAuth(me, token)).catch(() => logout()).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-blue-600"/>
    </div>
  )

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Navigate to="/upload" replace />} />
        <Route path="/upload"        element={<ProtectedRoute><UploadPage /></ProtectedRoute>} />
        <Route path="/seo"           element={<ProtectedRoute><SEOPage /></ProtectedRoute>} />
        <Route path="/review"        element={<ProtectedRoute><ReviewPage /></ProtectedRoute>} />
        <Route path="/export-links" element={<Layout><ExportLinksPage/></Layout>}/>
        <Route path="/submit-index" element={<Layout><SubmitIndexPage/></Layout>}/>
              <Route path="/internal-link" element={<ProtectedRoute><InternalLinkPage /></ProtectedRoute>} />
        <Route path="/admin/users"    element={<ProtectedRoute adminOnly><AdminUsersPage /></ProtectedRoute>} />
        <Route path="/admin/stores"   element={<ProtectedRoute adminOnly><StoresPage /></ProtectedRoute>} />
        <Route path="/admin/settings" element={<ProtectedRoute adminOnly><AdminSettingsPage /></ProtectedRoute>} />
        <Route path="/admin/jobs"     element={<ProtectedRoute adminOnly><JobManagerPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/upload" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
