import { Bot, WifiOff, Lock, Boxes } from 'lucide-react'

const STATS = [
  {
    icon: Bot,
    value: '10 AI Agents',
    label: 'Specialized for every clinical need',
  },
  {
    icon: WifiOff,
    value: 'Offline-First',
    label: 'Works without internet',
  },
  {
    icon: Lock,
    value: 'Privacy-Preserving',
    label: 'All data stored locally',
  },
  {
    icon: Boxes,
    value: 'Open Models',
    label: 'Powered by open medical AI',
  },
]

export default function StatsBar() {
  return (
    <section className="bg-white" aria-label="Key facts">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-x-6 gap-y-10 px-6 py-12 sm:py-14 lg:grid-cols-4">
        {STATS.map(({ icon: Icon, value, label }) => (
          <div key={value} className="flex flex-col items-center text-center">
            <span className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-teal-50 text-teal-600">
              <Icon className="h-5 w-5" aria-hidden="true" />
            </span>
            <div className="text-lg font-bold text-[#1A1A2E]">{value}</div>
            <div className="mt-1 text-sm text-muted-foreground">{label}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
