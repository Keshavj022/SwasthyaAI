'use client'

import { useEffect, useState } from 'react'
import { Download, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

/** Minimal typing for the non-standard beforeinstallprompt event. */
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>
}

const VISIT_KEY = 'swasthya_visit_count'
const DISMISS_KEY = 'swasthya_install_dismissed_until'
const MIN_VISITS = 3
const SUPPRESS_MS = 7 * 24 * 60 * 60 * 1000 // 7 days

function isSuppressed(): boolean {
  try {
    const until = Number(localStorage.getItem(DISMISS_KEY) || 0)
    return Number.isFinite(until) && until > Date.now()
  } catch {
    return false
  }
}

function recordVisit(): number {
  try {
    const count = Number(localStorage.getItem(VISIT_KEY) || 0) + 1
    localStorage.setItem(VISIT_KEY, String(count))
    return count
  } catch {
    return 0
  }
}

/**
 * Captures the browser's `beforeinstallprompt` event and surfaces a custom
 * "Install SwasthyaAI" prompt once the user has visited 3+ times. Dismissing
 * suppresses it for 7 days. Only renders when the app is installable (i.e. the
 * event fired and the app isn't already installed).
 */
export default function InstallPrompt() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return

    // Already running as an installed PWA -> never prompt.
    const standalone =
      window.matchMedia?.('(display-mode: standalone)')?.matches ||
      // iOS Safari
      (window.navigator as unknown as { standalone?: boolean }).standalone === true
    if (standalone) return

    const visits = recordVisit()

    const handler = (e: Event) => {
      // Stop Chrome's default mini-infobar; we present our own UI.
      e.preventDefault()
      setDeferred(e as BeforeInstallPromptEvent)
      if (visits >= MIN_VISITS && !isSuppressed()) {
        setVisible(true)
      }
    }

    const installedHandler = () => {
      setVisible(false)
      setDeferred(null)
    }

    window.addEventListener('beforeinstallprompt', handler)
    window.addEventListener('appinstalled', installedHandler)

    return () => {
      window.removeEventListener('beforeinstallprompt', handler)
      window.removeEventListener('appinstalled', installedHandler)
    }
  }, [])

  const handleInstall = async () => {
    if (!deferred) return
    try {
      await deferred.prompt()
      await deferred.userChoice
    } catch {
      // Ignore — user closed the native dialog.
    } finally {
      setDeferred(null)
      setVisible(false)
    }
  }

  const handleDismiss = () => {
    try {
      localStorage.setItem(DISMISS_KEY, String(Date.now() + SUPPRESS_MS))
    } catch {
      // localStorage unavailable — dismiss for this session only.
    }
    setVisible(false)
  }

  if (!visible || !deferred) return null

  return (
    <div
      className={cn(
        'fixed inset-x-0 bottom-0 z-50 p-4 sm:bottom-4 sm:left-auto sm:right-4 sm:max-w-sm',
        'animate-in slide-in-from-bottom-4 fade-in duration-300'
      )}
      role="dialog"
      aria-label="Install SwasthyaAI"
    >
      <div className="rounded-xl border bg-card text-card-foreground shadow-lg">
        <div className="flex items-start gap-3 p-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-teal-600 text-white">
            <Download className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold">Install SwasthyaAI</p>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Install the app for offline access and a faster, full-screen
              experience.
            </p>
          </div>
          <button
            type="button"
            onClick={handleDismiss}
            className="shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400"
            aria-label="Dismiss install prompt"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex gap-2 border-t p-3">
          <Button variant="ghost" size="sm" className="flex-1" onClick={handleDismiss}>
            Not now
          </Button>
          <Button
            size="sm"
            className="flex-1 bg-teal-600 hover:bg-teal-700"
            onClick={handleInstall}
          >
            <Download className="h-4 w-4" />
            Install
          </Button>
        </div>
      </div>
    </div>
  )
}
