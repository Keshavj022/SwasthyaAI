'use client'

import {
  LogIn,
  Brain,
  ShieldCheck,
  FolderOpen,
  CalendarClock,
  UserPlus,
  MessageSquareText,
  HeartPulse,
  CalendarCheck,
  Target,
  type LucideIcon,
} from 'lucide-react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'

interface Step {
  icon: LucideIcon
  text: string
}

const DOCTOR_STEPS: Step[] = [
  { icon: LogIn, text: 'Log in with your credentials' },
  { icon: Brain, text: 'Access the AI diagnostic assistant' },
  { icon: ShieldCheck, text: 'Check drug interactions instantly' },
  { icon: FolderOpen, text: 'View patient records & documents' },
  { icon: CalendarClock, text: 'Manage your schedule' },
]

const PATIENT_STEPS: Step[] = [
  { icon: UserPlus, text: 'Register with your health profile' },
  { icon: MessageSquareText, text: 'Describe your symptoms to SwasthyaAI' },
  { icon: HeartPulse, text: 'Get plain-language health guidance' },
  { icon: CalendarCheck, text: 'Book appointments with nearby doctors' },
  { icon: Target, text: 'Track your health goals daily' },
]

function Stepper({ steps }: { steps: Step[] }) {
  return (
    <ol className="relative mx-auto max-w-2xl space-y-2">
      {steps.map(({ icon: Icon, text }, i) => (
        <li key={text} className="flex items-start gap-4">
          <div className="flex flex-col items-center">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-teal-600 text-white shadow-sm">
              <Icon className="h-5 w-5" aria-hidden="true" />
            </span>
            {i < steps.length - 1 && (
              <span className="my-1 h-8 w-px bg-teal-200" aria-hidden="true" />
            )}
          </div>
          <div className="flex min-h-[44px] items-center">
            <span className="text-sm font-medium text-teal-600">Step {i + 1}</span>
            <span className="mx-2 text-muted-foreground" aria-hidden="true">
              ·
            </span>
            <span className="text-base text-[#1A1A2E]">{text}</span>
          </div>
        </li>
      ))}
    </ol>
  )
}

export default function HowItWorks() {
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-600">
            How it works
          </p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-[#1A1A2E] sm:text-4xl">
            For doctors and patients
          </h2>
        </div>

        <Tabs defaultValue="doctors" className="mt-12 flex flex-col items-center">
          <TabsList className="mb-10">
            <TabsTrigger value="doctors" className="px-6">
              For Doctors
            </TabsTrigger>
            <TabsTrigger value="patients" className="px-6">
              For Patients
            </TabsTrigger>
          </TabsList>

          <TabsContent value="doctors" className="w-full">
            <Stepper steps={DOCTOR_STEPS} />
          </TabsContent>
          <TabsContent value="patients" className="w-full">
            <Stepper steps={PATIENT_STEPS} />
          </TabsContent>
        </Tabs>
      </div>
    </section>
  )
}
