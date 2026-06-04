import { Skeleton } from '@/components/ui/skeleton'

interface TableRowSkeletonProps {
  /** Number of placeholder rows. */
  rows?: number
  /** Number of columns per row. */
  columns?: number
}

/**
 * Placeholder <tr> rows for tables in a loading state. Render inside a <tbody>:
 *
 *   <tbody><TableRowSkeleton rows={5} columns={4} /></tbody>
 */
export default function TableRowSkeleton({ rows = 5, columns = 4 }: TableRowSkeletonProps) {
  return (
    <>
      {Array.from({ length: rows }).map((_, r) => (
        <tr key={r} className="border-b border-gray-100" aria-hidden="true">
          {Array.from({ length: columns }).map((_, c) => (
            <td key={c} className="px-4 py-3">
              <Skeleton className={c === 0 ? 'h-4 w-3/4' : 'h-4 w-1/2'} />
            </td>
          ))}
        </tr>
      ))}
    </>
  )
}
