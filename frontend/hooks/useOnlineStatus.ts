'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

const PING_INTERVAL_MS = 30_000
const PING_TIMEOUT_MS = 5_000

export interface OnlineStatus {
  /** Browser-level connectivity (navigator.onLine). */
  isOnline: boolean
  /** Whether the backend health endpoint responded recently. */
  backendReachable: boolean
  /** Timestamp (ms) of the last backend reachability check, or null. */
  lastChecked: number | null
  /** Force an immediate backend reachability check. */
  refresh: () => void
}

/**
 * Tracks both browser connectivity (online/offline events) and whether the
 * SwasthyaAI backend is actually reachable (pings /api/health/ping every 30s).
 *
 * `backendReachable` is what the UI should key offline messaging off of, since
 * the device can be "online" while the backend is down or unreachable.
 */
export function useOnlineStatus(): OnlineStatus {
  const [isOnline, setIsOnline] = useState(true)
  const [backendReachable, setBackendReachable] = useState(true)
  const [lastChecked, setLastChecked] = useState<number | null>(null)
  const mountedRef = useRef(true)

  const checkBackend = useCallback(async () => {
    // If the browser says we're offline, skip the network round-trip.
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      if (mountedRef.current) {
        setBackendReachable(false)
        setLastChecked(Date.now())
      }
      return
    }

    try {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), PING_TIMEOUT_MS)
      const res = await fetch(`${API_BASE_URL}/api/health/ping`, {
        method: 'GET',
        signal: controller.signal,
        cache: 'no-store',
      })
      clearTimeout(timer)
      if (mountedRef.current) {
        setBackendReachable(res.ok)
        setLastChecked(Date.now())
      }
    } catch {
      if (mountedRef.current) {
        setBackendReachable(false)
        setLastChecked(Date.now())
      }
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true

    // Seed initial browser state.
    if (typeof navigator !== 'undefined') {
      setIsOnline(navigator.onLine)
    }

    const handleOnline = () => {
      setIsOnline(true)
      // Re-verify the backend as soon as the device comes back online.
      void checkBackend()
    }
    const handleOffline = () => {
      setIsOnline(false)
      setBackendReachable(false)
      setLastChecked(Date.now())
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Initial check + polling.
    void checkBackend()
    const interval = setInterval(() => void checkBackend(), PING_INTERVAL_MS)

    return () => {
      mountedRef.current = false
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      clearInterval(interval)
    }
  }, [checkBackend])

  return { isOnline, backendReachable, lastChecked, refresh: checkBackend }
}

export default useOnlineStatus
