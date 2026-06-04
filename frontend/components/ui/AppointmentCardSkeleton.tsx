import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface AppointmentCardSkeletonProps {
  /** Number of placeholder cards to render. */
  count?: number
  className?: string
}

/**
 * Loading placeholder mirroring the AppointmentCard layout: an avatar/icon, a
 * couple of text lines, a date/time chip and a status badge.
 */
export default function AppointmentCardSkeleton({
  count = 3,
  className,
}: AppointmentCardSkeletonProps) {
  return (
    <div className={cn('space-y-3', className)} aria-hidden="true">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 rounded-xl border border-gray-100 bg-white p-4 shadow-sm"
        >
          <Skeleton className="h-12 w-12 shrink-0 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-2/5" />
            <Skeleton className="h-3 w-3/5" />
            <Skeleton className="h-3 w-1/4" />
          </div>
          <div className="flex flex-col items-end gap-2">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
      ))}
    </div>
  )
}
