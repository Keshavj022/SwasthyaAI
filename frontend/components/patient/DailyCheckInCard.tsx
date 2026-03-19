'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useSubmitCheckIn } from '@/hooks/usePatients'

const MOODS = [
  { value: 1, emoji: '😢', label: 'Terrible' },
  { value: 2, emoji: '😕', label: 'Bad' },
  { value: 3, emoji: '😐', label: 'Okay' },
  { value: 4, emoji: '🙂', label: 'Good' },
  { value: 5, emoji: '😄', label: 'Great' },
]

const SYMPTOM_OPTIONS = ['Headache', 'Fatigue', 'Nausea', 'Pain', 'Fever', 'Cough', 'Other']

interface DailyCheckInCardProps {
  onSuccess: () => void
}

export default function DailyCheckInCard({ onSuccess }: DailyCheckInCardProps) {
  const { user } = useAuth()
  const submitCheckIn = useSubmitCheckIn()

  const [mood, setMood] = useState<number | null>(null)
  const [energy, setEnergy] = useState(5)
  const [sleep, setSleep] = useState(7)
  const [symptoms, setSymptoms] = useState<string[]>([])

  const toggleSymptom = (s: string) =>
    setSymptoms((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]))

  const handleSubmit = async () => {
    if (!user?.id || mood === null) return
    const moodScaled = mood * 2 // Convert 1-5 → 2-10 for backend 1-10 scale
    submitCheckIn.mutate(
      {
        patientId: user.id,
        data: { mood: moodScaled, energy, sleep, symptoms },
      },
      {
        onSuccess: () => {
          toast.success('Check-in saved! Keep up the great work.')
          onSuccess()
        },
        onError: () => {
          toast.error('Failed to save check-in. Please try again.')
        },
      }
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h2 className="text-base font-semibold text-gray-900 mb-4">How are you feeling today?</h2>

      {/* Mood */}
      <div className="mb-5">
        <p className="text-sm text-gray-600 mb-2">Mood</p>
        <div className="flex gap-3">
          {MOODS.map(({ value, emoji, label }) => (
            <button
              key={value}
              type="button"
              onClick={() => setMood(value)}
              title={label}
              className={`flex-1 py-2 rounded-xl text-2xl transition-all border-2 ${
                mood === value
                  ? 'border-teal-500 bg-teal-50 scale-105'
                  : 'border-gray-100 hover:border-gray-300'
              }`}
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>

      {/* Energy slider */}
      <div className="mb-5">
        <div className="flex justify-between items-center mb-1">
          <p className="text-sm text-gray-600">Energy level</p>
          <span className="text-sm font-semibold text-teal-600">{energy}/10</span>
        </div>
        <input
          type="range"
          min={1}
          max={10}
          value={energy}
          onChange={(e) => setEnergy(Number(e.target.value))}
          className="w-full accent-teal-500"
        />
      </div>

      {/* Sleep hours */}
      <div className="mb-5">
        <p className="text-sm text-gray-600 mb-1">Sleep hours last night</p>
        <input
          type="number"
          min={0}
          max={12}
          step={0.5}
          value={sleep}
          onChange={(e) => setSleep(Number(e.target.value))}
          className="w-24 px-3 py-1.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
      </div>

      {/* Symptoms */}
      <div className="mb-5">
        <p className="text-sm text-gray-600 mb-2">Any symptoms today?</p>
        <div className="flex flex-wrap gap-2">
          {SYMPTOM_OPTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => toggleSymptom(s)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                symptoms.includes(s)
                  ? 'border-teal-500 bg-teal-50 text-teal-700'
                  : 'border-gray-200 text-gray-600 hover:border-gray-400'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleSubmit}
        disabled={mood === null || submitCheckIn.isPending}
        className="w-full py-2.5 rounded-xl bg-teal-600 text-white font-medium text-sm hover:bg-teal-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
      >
        {submitCheckIn.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
        Save check-in
      </button>
    </div>
  )
}
