'use client'

interface SuggestedPromptsProps {
  role: 'patient' | 'doctor' | 'admin'
  onSelect: (prompt: string) => void
}

const PATIENT_PROMPTS = [
  'What are the side effects of Metformin?',
  'I have a headache and fever — what should I do?',
  'Book an appointment with a cardiologist',
  'Explain my last lab results',
  'How can I manage my blood pressure?',
]

const DOCTOR_PROMPTS = [
  'Analyze symptoms: chest pain, shortness of breath, 60yo male',
  'Check interactions: Warfarin, Aspirin, Ibuprofen',
  'Triage: patient with 39.5°C fever and rash',
  'Book follow-up for patient John Doe',
]

export function SuggestedPrompts({ role, onSelect }: SuggestedPromptsProps) {
  const prompts = role === 'doctor' ? DOCTOR_PROMPTS : PATIENT_PROMPTS

  return (
    <div className="px-4 py-3 border-t border-gray-100 bg-gray-50">
      <p className="text-xs text-gray-500 mb-2 font-medium">Suggested questions</p>
      <div className="flex flex-wrap gap-2">
        {prompts.map((prompt) => (
          <button
            key={prompt}
            onClick={() => onSelect(prompt)}
            className="text-xs px-3 py-1.5 rounded-full bg-white border border-gray-200 text-gray-700
                       hover:border-teal-400 hover:text-teal-700 hover:bg-teal-50 transition-colors
                       shadow-sm text-left"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  )
}
