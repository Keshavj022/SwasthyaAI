import { cn } from '@/lib/utils'

interface MessageBubbleSkeletonProps {
  className?: string
}

/**
 * Typing-indicator style placeholder shown while the assistant is generating a
 * reply. Three pulsing dots inside an assistant-aligned bubble.
 */
export default function MessageBubbleSkeleton({ className }: MessageBubbleSkeletonProps) {
  return (
    <div
      className={cn('flex w-full justify-start', className)}
      role="status"
      aria-label="Assistant is typing"
    >
      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-sm bg-gray-100 px-4 py-3">
        <span className="h-2 w-2 animate-bounce rounded-full bg-teal-500 [animation-delay:-0.3s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-teal-500 [animation-delay:-0.15s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-teal-500" />
        <span className="sr-only">Assistant is typing…</span>
      </div>
    </div>
  )
}
