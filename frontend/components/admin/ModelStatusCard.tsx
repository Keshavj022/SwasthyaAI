'use client'

import { Cpu, CheckCircle2, FlaskConical, PowerOff } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AIModelStatus } from '@/types'

interface ModelStatusCardProps {
  model: AIModelStatus
  className?: string
}

type State = 'loaded' | 'stub' | 'disabled'

function resolveState(model: AIModelStatus): State {
  if (!model.enabled) return 'disabled'
  if (model.loaded && !model.stub) return 'loaded'
  return 'stub'
}

const STATE_META: Record<
  State,
  { label: string; badge: string; dot: string; icon: typeof CheckCircle2; ring: string }
> = {
  loaded: {
    label: 'Loaded',
    badge: 'bg-green-100 text-green-700 border-green-200',
    dot: 'bg-green-500',
    icon: CheckCircle2,
    ring: 'border-green-100',
  },
  stub: {
    label: 'Stub mode',
    badge: 'bg-amber-100 text-amber-700 border-amber-200',
    dot: 'bg-amber-500',
    icon: FlaskConical,
    ring: 'border-amber-100',
  },
  disabled: {
    label: 'Disabled',
    badge: 'bg-gray-100 text-gray-600 border-gray-200',
    dot: 'bg-gray-400',
    icon: PowerOff,
    ring: 'border-gray-100',
  },
}

export default function ModelStatusCard({ model, className }: ModelStatusCardProps) {
  const state = resolveState(model)
  const meta = STATE_META[state]
  const Icon = meta.icon

  return (
    <div
      className={cn(
        'bg-white rounded-xl border p-4 shadow-sm transition-colors',
        meta.ring,
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div
            className={cn(
              'w-9 h-9 rounded-lg flex items-center justify-center shrink-0',
              state === 'loaded'
                ? 'bg-green-50 text-green-600'
                : state === 'stub'
                  ? 'bg-amber-50 text-amber-600'
                  : 'bg-gray-50 text-gray-400'
            )}
          >
            <Cpu className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-900 truncate">{model.name}</p>
            {model.repoId && (
              <p className="text-xs text-gray-400 truncate font-mono">{model.repoId}</p>
            )}
          </div>
        </div>
        <span
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold shrink-0',
            meta.badge
          )}
        >
          <span className={cn('w-1.5 h-1.5 rounded-full', meta.dot)} />
          {meta.label}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <Flag label="Enabled" on={model.enabled} />
        <Flag label="Loaded" on={model.loaded} />
        <Flag label="Live" on={model.enabled && model.loaded && !model.stub} />
      </div>

      {state === 'stub' && (
        <div className="mt-3 flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-100 px-3 py-2">
          <Icon className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <p className="text-xs text-amber-700 leading-snug">
            Running in demo/stub mode — outputs are illustrative, not real model inferences.
          </p>
        </div>
      )}

      {model.device && (
        <p className="mt-2.5 text-xs text-gray-400">
          Device: <span className="font-medium text-gray-600">{model.device}</span>
        </p>
      )}
    </div>
  )
}

function Flag({ label, on }: { label: string; on: boolean }) {
  return (
    <div className="rounded-lg bg-gray-50 py-1.5">
      <p className="text-[10px] uppercase tracking-wide text-gray-400">{label}</p>
      <p className={cn('text-xs font-semibold', on ? 'text-green-600' : 'text-gray-400')}>
        {on ? 'Yes' : 'No'}
      </p>
    </div>
  )
}
