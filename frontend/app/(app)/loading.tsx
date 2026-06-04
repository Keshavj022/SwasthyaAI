import { Skeleton } from '@/components/ui/skeleton'
import StatCardSkeleton from '@/components/ui/StatCardSkeleton'

/**
 * Route-segment loading UI for the authenticated (app) area. Shown by Next.js
 * during navigation/streaming before a page's content is ready. Approximates a
 * typical dashboard shell so the transition feels stable.
 */
export default function AppLoading() {
  return (
    <div className="flex-1 overflow-auto p-6" aria-busy="true" aria-live="polite">
      <span className="sr-only">Loading…</span>

      {/* Page header */}
      <div className="mb-6 space-y-2">
        <Skeleton className="h-7 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>

      {/* Stat row */}
      <StatCardSkeleton count={4} className="mb-6" />

      {/* Content block */}
      <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
        <Skeleton className="mb-4 h-5 w-40" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-10 w-10 shrink-0 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
