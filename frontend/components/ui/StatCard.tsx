import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'

type Color = 'teal' | 'blue' | 'green' | 'amber' | 'red'

interface Trend {
  direction: 'up' | 'down' | 'neutral'
  value: string
}

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  trend?: Trend
  color?: Color
  className?: string
}

const COLOR_MAP: Record<Color, { bg: string; text: string; icon: string }> = {
  teal:  { bg: 'bg-teal-50',  text: 'text-teal-700',  icon: 'bg-teal-100 text-teal-600' },
  blue:  { bg: 'bg-blue-50',  text: 'text-blue-700',  icon: 'bg-blue-100 text-blue-600' },
  green: { bg: 'bg-green-50', text: 'text-green-700', icon: 'bg-green-100 text-green-600' },
  amber: { bg: 'bg-amber-50', text: 'text-amber-700', icon: 'bg-amber-100 text-amber-600' },
  red:   { bg: 'bg-red-50',   text: 'text-red-700',   icon: 'bg-red-100 text-red-600' },
}

const TREND_ICON: Record<Trend['direction'], React.ComponentType<{ className?: string }>> = {
  up:      TrendingUp,
  down:    TrendingDown,
  neutral: Minus,
}

const TREND_COLOR: Record<Trend['direction'], string> = {
  up:      'text-green-600',
  down:    'text-red-500',
  neutral: 'text-gray-400',
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  color = 'teal',
  className,
}: StatCardProps) {
  const colors = COLOR_MAP[color]
  const TrendIcon = trend ? TREND_ICON[trend.direction] : null

  return (
    <div className={cn('bg-white rounded-xl border border-gray-100 p-5 shadow-sm', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-500 truncate">{title}</p>
          <p className="mt-1.5 text-2xl font-bold text-gray-900 leading-none">{value}</p>
          {subtitle && (
            <p className="mt-1 text-xs text-gray-400">{subtitle}</p>
          )}
          {trend && TrendIcon && (
            <div className={cn('mt-2 flex items-center gap-1 text-xs font-medium', TREND_COLOR[trend.direction])}>
              <TrendIcon className="w-3.5 h-3.5" />
              <span>{trend.value}</span>
            </div>
          )}
        </div>
        <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ml-3', colors.icon)}>
          {icon}
        </div>
      </div>
    </div>
  )
}
