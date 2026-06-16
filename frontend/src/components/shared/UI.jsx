import { clsx } from 'clsx'

export function Button({ children, variant = 'primary', size = 'md', className, ...props }) {
  const base = 'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary:  'bg-brand text-white hover:bg-brand-dark',
    danger:   'bg-red-600 text-white hover:bg-red-700',
    outline:  'border border-gray-300 text-gray-700 hover:bg-gray-50',
    ghost:    'text-gray-600 hover:bg-gray-100',
    success:  'bg-green-600 text-white hover:bg-green-700',
  }
  const sizes = {
    sm: 'text-sm px-3 py-1.5',
    md: 'text-sm px-4 py-2',
    lg: 'text-base px-5 py-2.5',
  }
  return (
    <button className={clsx(base, variants[variant], sizes[size], className)} {...props}>
      {children}
    </button>
  )
}

export function Card({ children, className }) {
  return <div className={clsx('bg-white rounded-xl border border-gray-200 shadow-sm', className)}>{children}</div>
}

export function Input({ label, error, className, ...props }) {
  return (
    <div className="space-y-1">
      {label && <label className="block text-sm font-medium text-gray-700">{label}</label>}
      <input
        className={clsx(
          'w-full px-3 py-2 text-sm border rounded-lg outline-none transition-colors',
          'border-gray-300 focus:border-brand focus:ring-1 focus:ring-brand',
          error && 'border-red-500',
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
}

export function Select({ label, children, className, ...props }) {
  return (
    <div className="space-y-1">
      {label && <label className="block text-sm font-medium text-gray-700">{label}</label>}
      <select
        className={clsx(
          'w-full px-3 py-2 text-sm border border-gray-300 rounded-lg outline-none',
          'focus:border-brand focus:ring-1 focus:ring-brand bg-white',
          className
        )}
        {...props}
      >
        {children}
      </select>
    </div>
  )
}

export function Badge({ children, variant = 'gray' }) {
  const variants = {
    gray:    'bg-gray-100 text-gray-700',
    blue:    'bg-blue-100 text-blue-700',
    green:   'bg-green-100 text-green-700',
    red:     'bg-red-100 text-red-700',
    yellow:  'bg-yellow-100 text-yellow-700',
    pending: 'bg-yellow-100 text-yellow-700',
    running: 'bg-blue-100 text-blue-700',
    done:    'bg-green-100 text-green-700',
    failed:  'bg-red-100 text-red-700',
  }
  return (
    <span className={clsx('inline-block px-2 py-0.5 text-xs font-medium rounded-full', variants[variant] || variants.gray)}>
      {children}
    </span>
  )
}

export function LogBox({ log }) {
  return (
    <pre className="bg-gray-900 text-green-400 text-xs p-4 rounded-lg h-48 overflow-y-auto whitespace-pre-wrap font-mono">
      {log || 'Chờ bắt đầu...'}
    </pre>
  )
}

export function Spinner({ size = 'md' }) {
  const s = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-8 w-8' }
  return <div className={clsx('animate-spin rounded-full border-2 border-gray-300 border-t-brand', s[size])} />
}
