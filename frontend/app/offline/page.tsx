'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { CloudOff, RefreshCw, LayoutDashboard, MessageSquare, CalendarDays } from 'lucide-react'
import { Button } from '@/components/ui/button'

const OFFLINE_PAGES = [
  {
    href: '/dashboard/patient',
    label: 'Dashboard',
    description: 'Your most recent overview',
    icon: LayoutDashboard,
  },
  {
    href: '/chat',
    label: 'Chat history',
    description: 'Previously loaded conversations',
    icon: MessageSquare,
  },
  {
    href: '/appointments',
    label: 'Appointments',
    description: 'Cached appointment list',
    icon: CalendarDays,
  },
]

export default function OfflinePage() {
  const router = useRouter()

  const handleRetry = () => {
    if (typeof navigator !== 'undefined' && navigator.onLine) {
      router.back()
    } else {
      // Force a reload; the SW will serve a fresh page once connectivity returns.
      window.location.reload()
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-6 py-12">
      <div className="w-full max-w-md text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-50 text-teal-600">
          <CloudOff className="h-8 w-8" aria-hidden="true" />
        </div>

        <h1 className="text-2xl font-semibold tracking-tight text-gray-900">
          You&apos;re offline
        </h1>
        <p className="mt-2 text-sm text-gray-600">
          SwasthyaAI can&apos;t reach the network right now. Live AI features are
          paused, but you can still open recently visited pages from your cache.
        </p>

        <div className="mt-8 space-y-2 text-left">
          <p className="px-1 text-xs font-medium uppercase tracking-wide text-gray-400">
            Available offline
          </p>
          {OFFLINE_PAGES.map(({ href, label, description, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 transition-colors hover:border-teal-300 hover:bg-teal-50/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-teal-50 text-teal-600">
                <Icon className="h-4 w-4" />
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-medium text-gray-900">{label}</span>
                <span className="block truncate text-xs text-gray-500">{description}</span>
              </span>
            </Link>
          ))}
        </div>

        <Button
          onClick={handleRetry}
          className="mt-8 w-full bg-teal-600 hover:bg-teal-700"
        >
          <RefreshCw className="h-4 w-4" />
          Try again
        </Button>

        <p className="mt-4 text-xs text-gray-400">
          Cached data may be out of date. Always confirm clinical information once
          you&apos;re back online.
        </p>
      </div>
    </main>
  )
}
