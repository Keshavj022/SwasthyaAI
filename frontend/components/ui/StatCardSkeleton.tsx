import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface StatCardSkeletonProps {
  /** Number of stat-card placeholders to render. */
  count?: number
  className?: string
}

/**
 * Shimmer placeholder matching the StatCard layout: a title line, a large value,
 * a subtitle and the rounded icon tile on the right.
 */
export default function StatCardSkeleton({ count = 1, className }: StatCardSkeletonProps) {
  const cards = Array.from({ length: count }).map((_, i) => (
    <div
      key={i}
      className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm"
      aria-hidden="true"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <Skeleton className="h-3.5 w-24" />
          <Skeleton className="h-7 w-16" />
          <Skeleton className="h-3 w-20" />
        </div>
        <Skeleton className="ml-3 h-10 w-10 shrink-0 rounded-lg" />
      </div>
    </div>
  ))

  if (count === 1) {
    return <div className={className}>{cards}</div>
  }

  return (
    <div className={cn('grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4', className)}>
      {cards}
    </div>
  )
}
