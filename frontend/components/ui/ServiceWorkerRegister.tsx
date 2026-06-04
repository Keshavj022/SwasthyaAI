'use client'

import { useEffect } from 'react'

/**
 * Registers the hand-written service worker (/sw.js) on mount, in production
 * only. Renders nothing.
 *
 * NOTE: The spine-wired `OfflineBanner` (rendered by app/(app)/layout.tsx)
 * already registers the service worker on mount, so adding this component is
 * usually unnecessary. It is exported here for cases where SW registration is
 * wanted outside the authenticated app shell (e.g. the public landing page).
 * To use it, render <ServiceWorkerRegister /> from a client component or a
 * layout you control — the spine layout files must NOT be edited.
 */
export default function ServiceWorkerRegister() {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'production') return
    if (typeof window === 'undefined') return
    if (!('serviceWorker' in navigator)) return

    const register = () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // Non-fatal — the app remains fully functional while online.
      })
    }

    if (document.readyState === 'complete') {
      register()
    } else {
      window.addEventListener('load', register, { once: true })
      return () => window.removeEventListener('load', register)
    }
  }, [])

  return null
}
