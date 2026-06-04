import { ShieldCheck, Database, FileWarning, Siren, ClipboardList } from 'lucide-react'

const POINTS = [
  {
    icon: Database,
    text: 'All data stored locally on-device (SQLite)',
  },
  {
    icon: FileWarning,
    text: 'Every AI output includes safety disclaimers',
  },
  {
    icon: Siren,
    text: 'Emergency detection with immediate escalation',
  },
  {
    icon: ClipboardList,
    text: 'Complete audit trail of all AI interactions',
  },
]

export default function SafetyPrivacy() {
  return (
    <section className="bg-gray-50 py-20 sm:py-24">
      <div className="mx-auto max-w-4xl px-6 text-center">
        <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-50 text-teal-600">
          <ShieldCheck className="h-9 w-9" aria-hidden="true" />
        </span>

        <h2 className="mt-6 text-3xl font-bold tracking-tight text-[#1A1A2E] sm:text-4xl">
          Built with safety at its core
        </h2>

        <ul className="mx-auto mt-12 grid max-w-2xl grid-cols-1 gap-4 text-left sm:grid-cols-2">
          {POINTS.map(({ icon: Icon, text }) => (
            <li
              key={text}
              className="flex items-start gap-3 rounded-xl border border-border bg-white p-5 shadow-sm"
            >
              <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-600">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <span className="text-sm font-medium leading-relaxed text-[#1A1A2E]">
                {text}
              </span>
            </li>
          ))}
        </ul>

        <p className="mx-auto mt-10 max-w-2xl rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900">
          <strong className="font-semibold">SwasthyaAI is a clinical decision SUPPORT tool.</strong>{' '}
          It does not replace a qualified healthcare professional.
        </p>
      </div>
    </section>
  )
}
