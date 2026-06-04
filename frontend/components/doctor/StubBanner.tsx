'use client'

import { FlaskConical } from 'lucide-react'

interface Props {
  /** Optional note from the backend (data.stub_note) explaining why output is unverified. */
  note?: string
  className?: string
}

/**
 * Shown whenever an AI agent returns `stub_mode` / `isStub`. Makes it
 * unambiguous that the output is demo / unverified and must NOT be treated as
 * an authoritative clinical finding.
 */
export default function StubBanner({ note, className = '' }: Props) {
  return (
    <div
      role="status"
      className={`flex items-start gap-2 p-3 rounded-xl bg-orange-50 border border-orange-200 ${className}`}
    >
      <FlaskConical className="w-4 h-4 text-orange-500 mt-0.5 shrink-0" />
      <div className="min-w-0">
        <p className="text-xs font-semibold text-orange-800">AI model not loaded — demo output</p>
        <p className="text-xs text-orange-700 mt-0.5">
          {note ??
            'This is non-authoritative sample output. Do not use for clinical decisions.'}
        </p>
      </div>
    </div>
  )
}
