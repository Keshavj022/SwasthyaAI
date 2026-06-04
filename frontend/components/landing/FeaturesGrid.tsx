import {
  Stethoscope,
  Pill,
  Microscope,
  CalendarDays,
  Dna,
  ImageIcon,
} from 'lucide-react'

const FEATURES = [
  {
    icon: Stethoscope,
    title: 'Symptom Assessment',
    description: 'Check symptoms & get triage guidance in plain language.',
  },
  {
    icon: Pill,
    title: 'Drug Info & Interactions',
    description: 'Safe medication guidance and interaction checks.',
  },
  {
    icon: Microscope,
    title: 'Diagnostic Support',
    description: 'Differential diagnosis aid for clinicians.',
  },
  {
    icon: CalendarDays,
    title: 'Appointment Scheduling',
    description: 'Book & manage appointments with available doctors.',
  },
  {
    icon: Dna,
    title: 'Lab Results Interpreter',
    description: 'Understand your reports with clear explanations.',
  },
  {
    icon: ImageIcon,
    title: 'Image Analysis',
    description: 'X-Ray & scan review support for faster reads.',
  },
]

export default function FeaturesGrid() {
  return (
    <section id="features" className="scroll-mt-16 bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-600">
            What SwasthyaAI does
          </p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-[#1A1A2E] sm:text-4xl">
            A complete AI system for healthcare
          </h2>
        </div>

        <ul className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, description }) => (
            <li key={title}>
              <div className="group h-full rounded-xl border border-border bg-white p-6 shadow-sm transition-all duration-200 motion-safe:hover:-translate-y-1 hover:border-teal-200 hover:shadow-lg">
                <span className="flex h-12 w-12 items-center justify-center rounded-lg bg-teal-50 text-teal-600 transition-colors group-hover:bg-teal-600 group-hover:text-white">
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </span>
                <h3 className="mt-5 text-lg font-semibold text-[#1A1A2E]">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {description}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
