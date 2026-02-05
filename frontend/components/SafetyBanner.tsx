interface SafetyBannerProps {
  /** Controls severity styling. */
  level: "emergency" | "warning" | "info"
  /** Primary message shown in bold. */
  title: string
  /** Optional supporting text beneath the title. */
  description?: string
  /** Optional list of red-flag strings to surface individually. */
  redFlags?: string[]
  /** Accessible label override for the banner region. */
  ariaLabel?: string
}

const config = {
  emergency: {
    container: "bg-red-50 border-red-300 text-red-900",
    icon: (
      <svg aria-hidden="true" className="w-5 h-5 text-red-600 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
      </svg>
    ),
    flagDot: "bg-red-500",
  },
  warning: {
    container: "bg-yellow-50 border-yellow-300 text-yellow-900",
    icon: (
      <svg aria-hidden="true" className="w-5 h-5 text-yellow-600 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
      </svg>
    ),
    flagDot: "bg-yellow-600",
  },
  info: {
    container: "bg-blue-50 border-blue-300 text-blue-900",
    icon: (
      <svg aria-hidden="true" className="w-5 h-5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
      </svg>
    ),
    flagDot: "bg-blue-500",
  },
} as const

export default function SafetyBanner({
  level,
  title,
  description,
  redFlags,
  ariaLabel,
}: SafetyBannerProps) {
  const styles = config[level]

  return (
    <div
      role="alert"
      aria-label={ariaLabel ?? title}
      className={`rounded-lg border p-4 ${styles.container}`}
    >
      {/* Header row */}
      <div className="flex items-start gap-3">
        {styles.icon}
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm leading-5">{title}</p>
          {description && (
            <p className="mt-1 text-sm leading-5 opacity-90">{description}</p>
          )}
        </div>
      </div>

      {/* Red-flag list */}
      {redFlags && redFlags.length > 0 && (
        <ul
          className="mt-3 ml-8 space-y-1"
          aria-label="Identified red flags"
        >
          {redFlags.map((flag, i) => (
            <li key={i} className="flex items-center gap-2 text-sm">
              <span
                className={`w-1.5 h-1.5 rounded-full ${styles.flagDot} shrink-0`}
                aria-hidden="true"
              />
              {flag}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
