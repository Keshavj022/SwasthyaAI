'use client'

import { Search, Bell, Menu } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useSystemHealth } from '@/hooks/useSystemHealth'
import { cn } from '@/lib/utils'

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((p) => p[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

interface HeaderProps {
  title?: string
}

export default function Header({ title }: HeaderProps) {
  const { user } = useAuth()
  const { data: health, isLoading } = useSystemHealth()

  const statusColor = isLoading
    ? 'bg-yellow-400'
    : health?.status === 'healthy'
      ? 'bg-green-500'
      : 'bg-red-500'

  const statusLabel = isLoading
    ? 'Checking…'
    : health?.status === 'healthy'
      ? 'System healthy'
      : 'System degraded'

  return (
    <header className="h-16 border-b border-gray-200 bg-white flex items-center gap-4 px-4 md:px-6 shrink-0">
      {/* Mobile hamburger (triggers the Sheet in Sidebar) */}
      <button
        className="md:hidden p-2 -ml-1 rounded-lg hover:bg-gray-100 text-gray-500"
        aria-label="Open navigation"
        onClick={() => {
          const trigger = document.getElementById('sidebar-mobile-trigger')
          trigger?.click()
        }}
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Page title */}
      {title && (
        <h1 className="text-base font-semibold text-gray-900 hidden sm:block shrink-0">{title}</h1>
      )}

      {/* Search bar */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="search"
            placeholder="Search patients, records…"
            className="w-full pl-9 pr-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent placeholder:text-gray-400"
          />
        </div>
      </div>

      <div className="ml-auto flex items-center gap-3">
        {/* System status */}
        <button
          title={statusLabel}
          className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors"
        >
          <span className={cn('w-2 h-2 rounded-full shrink-0', statusColor)} />
          <span className="hidden sm:inline">{isLoading ? 'Checking' : health?.status === 'healthy' ? 'Online' : 'Degraded'}</span>
        </button>

        {/* Notification bell */}
        <button className="relative p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
            3
          </span>
        </button>

        {/* User avatar */}
        {user && (
          <div className="w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center text-white text-xs font-bold shrink-0 cursor-pointer">
            {getInitials(user.name)}
          </div>
        )}
      </div>
    </header>
  )
}
