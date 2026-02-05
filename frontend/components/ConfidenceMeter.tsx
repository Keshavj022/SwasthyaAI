/**
 * Maps directly to the backend's ConfidenceLevel enum:
 *   high     → 80-100%  → green
 *   moderate → 50-79%   → yellow
 *   low      → 20-49%   → orange
 *   very_low → 0-19%    → red
 */

interface ConfidenceMeterProps {
  /** 0 – 100 integer score (backend returns `confidence.score` in this range). */
  score: number
  /** Display level string from the backend (high | moderate | low | very_low). */
  level: "high" | "moderate" | "low" | "very_low"
  /** Render as a compact inline badge instead of the full bar. */
  compact?: boolean
}

const tiers = {
  high:     { label: "High",      barColor: "bg-green-500",  textColor: "text-green-700",  bgColor: "bg-green-100" },
  moderate: { label: "Moderate",  barColor: "bg-yellow-500", textColor: "text-yellow-700", bgColor: "bg-yellow-100" },
  low:      { label: "Low",       barColor: "bg-orange-500", textColor: "text-orange-700", bgColor: "bg-orange-100" },
  very_low: { label: "Very Low",  barColor: "bg-red-500",    textColor: "text-red-700",    bgColor: "bg-red-100" },
} as const

export default function ConfidenceMeter({
  score,
  level,
  compact = false,
}: ConfidenceMeterProps) {
  const clamped = Math.max(0, Math.min(100, score))
  const tier = tiers[level]

  /* ── Compact badge variant ─────────────────────────────── */
  if (compact) {
    return (
      <span
        role="meter"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Confidence: ${tier.label} (${clamped}%)`}
        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${tier.bgColor} ${tier.textColor}`}
      >
        <span
          className={`w-1.5 h-1.5 rounded-full ${tier.barColor}`}
          aria-hidden="true"
        />
        {clamped}%
      </span>
    )
  }

  /* ── Full bar variant ──────────────────────────────────── */
  return (
    <div
      role="meter"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Confidence: ${tier.label} (${clamped}%)`}
      className="space-y-1.5"
    >
      {/* Label row */}
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700">Confidence</span>
        <span className={`font-semibold ${tier.textColor}`}>
          {tier.label} &middot; {clamped}%
        </span>
      </div>

      {/* Bar */}
      <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${tier.barColor}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  )
}
