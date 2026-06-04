'use client'

import { useEffect } from 'react'
import { AlertTriangle, RotateCcw } from 'lucide-react'

/**
 * Route-segment error UI for the authenticated (app) area. Next.js renders this
 * automatically when a child route throws during render or data fetching, and
 * provides `reset()` to re-attempt rendering the segment.
 */
export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error('[app/error] Route error:', error)
  }, [error])

  const isDev = process.env.NODE_ENV !== 'production'

  return (
    <div
      role="alert"
      className="flex flex-1 items-center justify-center overflow-auto p-6"
    >
      <div className="w-full max-w-md rounded-2xl border border-gray-100 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-500">
          <AlertTriangle className="h-7 w-7" aria-hidden="true" />
        </div>
        <h2 className="text-lg font-semibold text-gray-900">
          We hit a snag loading this page
        </h2>
        <p className="mt-2 text-sm text-gray-500">
          Something went wrong while loading this section. You can retry without
          losing your place.
        </p>

        {isDev && error?.message && (
          <pre className="mt-4 max-h-40 overflow-auto whitespace-pre-wrap rounded-lg bg-gray-900 p-3 text-left text-xs text-red-300">
            {error.message}
            {error.digest ? `\n\ndigest: ${error.digest}` : ''}
          </pre>
        )}

        <button
          type="button"
          onClick={reset}
          className="mt-6 inline-flex items-center justify-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2"
        >
          <RotateCcw className="h-4 w-4" aria-hidden="true" />
          Try again
        </button>
      </div>
    </div>
  )
}
