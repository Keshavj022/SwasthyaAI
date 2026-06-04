'use client'

import { useEffect, useState } from 'react'
import { WifiOff, X } from 'lucide-react'
import { useOnlineStatus } from '@/hooks/useOnlineStatus'
import { cn } from '@/lib/utils'

/**
 * Amber banner shown when the backend is unreachable (offline mode).
 *
 * This component is rendered by app/(app)/layout.tsx (spine-wired), so it also
 * doubles as the registration point for the service worker — registering here
 * avoids any edits to the protected layout files.
 */
export default function OfflineBanner() {
  const { backendReachable } = useOnlineStatus()
  const [dismissed, setDismissed] = useState(false)

  // Register the service worker once on mount (production only).
  useEffect(() => {
    if (process.env.NODE_ENV !== 'production') return
    if (typeof window === 'undefined') return
    if (!('serviceWorker' in navigator)) return

    const register = () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // Registration failures are non-fatal; the app still works online.
      })
    }

    if (document.readyState === 'complete') {
      register()
    } else {
      window.addEventListener('load', register, { once: true })
      return () => window.removeEventListener('load', register)
    }
  }, [])

  // Re-show the banner if connectivity drops again after a dismissal.
  useEffect(() => {
    if (backendReachable) setDismissed(false)
  }, [backendReachable])

  const visible = !backendReachable && !dismissed

  return (
    <div
      aria-live="polite"
      className={cn(
        'overflow-hidden transition-all duration-300 ease-in-out',
        visible ? 'max-h-20 opacity-100' : 'max-h-0 opacity-0'
      )}
    >
      <div className="flex items-center gap-3 border-b border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-900">
        <WifiOff className="h-4 w-4 shrink-0 text-amber-600" aria-hidden="true" />
        <p className="flex-1 leading-snug">
          <span className="font-medium">Running in offline mode</span>
          {' — '}
          AI features may be limited. Showing cached data where available.
        </p>
        <button
          type="button"
          onClick={() => setDismissed(true)}
          className="shrink-0 rounded-md p-1 text-amber-600 transition-colors hover:bg-amber-100 hover:text-amber-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
          aria-label="Dismiss offline notice"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
