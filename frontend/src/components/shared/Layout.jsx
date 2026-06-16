import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/auth'
import { Upload, FileText, Star, Settings, Users, LogOut, Package, Link, Activity, Store, Download } from 'lucide-react'
import { clsx } from 'clsx'

const NAV = [
  { to: '/upload',        label: 'Upload SP',     icon: Upload   },
  { to: '/seo',           label: 'SEO',           icon: FileText },
  { to: '/review',        label: 'Fake Review',   icon: Star     },
  { to: '/internal-link', label: 'Internal Link', icon: Link     },
  { to: '/export-links',   label: 'Export Links',   icon: Download  },
]
const ADMIN_NAV = [
  { to: '/admin/users',    label: 'Quản lý User',  icon: Users    },
  { to: '/admin/stores',   label: 'Quản lý Store', icon: Store    },
  { to: '/admin/jobs',     label: 'Job Manager',   icon: Activity },
  { to: '/admin/settings', label: 'Cài đặt',       icon: Settings },
]

export default function Layout({ children }) {
  const user          = useAuthStore(s => s.user)
  const logout        = useAuthStore(s => s.logout)
  const selectedStore = useAuthStore(s => s.selectedStore)
  const navigate = useNavigate()
  const isAdmin  = user?.is_admin === true || user?.is_admin === 'true'

  return (
    <div className="flex min-h-screen bg-gray-50">
      <aside className="w-56 bg-slate-900 flex flex-col">
        <div className="px-5 py-5 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand rounded-lg flex items-center justify-center">
              <Package size={16} className="text-white"/>
            </div>
            <span className="text-white font-bold text-sm">WooMMO Web</span>
          </div>
          <p className="text-slate-400 text-xs mt-1 truncate">{user?.username}</p>
          {selectedStore && (
            <p className="text-green-400 text-xs mt-0.5 truncate">🏪 {selectedStore.name}</p>
          )}
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to}
              className={({ isActive }) => clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                isActive ? 'bg-brand text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}>
              <Icon size={16}/>{label}
            </NavLink>
          ))}
          {isAdmin && (
            <>
              <div className="pt-3 pb-1">
                <p className="text-xs text-slate-500 px-3 font-medium uppercase tracking-wider">Admin</p>
              </div>
              {ADMIN_NAV.map(({ to, label, icon: Icon }) => (
                <NavLink key={to} to={to}
                  className={({ isActive }) => clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                    isActive ? 'bg-brand text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  )}>
                  <Icon size={16}/>{label}
                </NavLink>
              ))}
            </>
          )}
        </nav>
        <div className="px-3 py-4 border-t border-slate-700">
          <button onClick={() => { logout(); navigate('/login') }}
            className="flex items-center gap-3 px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg w-full transition-colors">
            <LogOut size={16}/> Đăng xuất
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}
