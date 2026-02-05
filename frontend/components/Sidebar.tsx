'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface NavItem {
  name: string
  href: string
  icon: string
  description: string
}

const navItems: NavItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: '📊',
    description: 'System overview and metrics'
  },
  {
    name: 'Chat',
    href: '/chat',
    icon: '💬',
    description: 'Medical Q&A and communication'
  },
  {
    name: 'Diagnostics',
    href: '/diagnostics',
    icon: '🔬',
    description: 'Differential diagnosis support'
  },
  {
    name: 'Imaging',
    href: '/imaging',
    icon: '🏥',
    description: 'Medical image analysis'
  },
  {
    name: 'Voice',
    href: '/voice',
    icon: '🎙️',
    description: 'Clinical dictation and transcription'
  },
  {
    name: 'Memory',
    href: '/memory',
    icon: '🧠',
    description: 'Patient history and context'
  },
  {
    name: 'Audit',
    href: '/audit',
    icon: '📋',
    description: 'System logs and compliance'
  }
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      {/* Logo/Branding */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <div className="text-2xl">🏥</div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Hospital AI</h1>
            <p className="text-xs text-gray-500">Offline-First System</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors
                ${isActive
                  ? 'bg-blue-50 text-blue-700 font-medium'
                  : 'text-gray-700 hover:bg-gray-50'
                }
              `}
            >
              <span className="text-xl">{item.icon}</span>
              <div className="flex-1">
                <div className={isActive ? 'font-semibold' : 'font-medium'}>
                  {item.name}
                </div>
                <div className="text-xs text-gray-500">
                  {item.description}
                </div>
              </div>
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 space-y-1">
          <div className="flex items-center justify-between">
            <span>Version</span>
            <span className="font-mono">0.1.0</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Environment</span>
            <span className="font-mono text-green-600">Development</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
