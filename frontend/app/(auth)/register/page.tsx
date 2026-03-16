'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Eye, EyeOff, Stethoscope, User, Shield, Loader2 } from 'lucide-react'
import { authApi } from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'

const SPECIALTIES = [
  'General Practice', 'Cardiology', 'Neurology', 'Orthopedics',
  'Pediatrics', 'Dermatology', 'Radiology', 'Oncology', 'Psychiatry',
]

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

const schema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Enter a valid email'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/\d/, 'Password must contain at least one number'),
  confirm_password: z.string(),
  role: z.enum(['patient', 'doctor', 'admin']),
  // Patient fields
  date_of_birth: z.string().optional(),
  blood_group: z.string().optional(),
  // Doctor fields
  specialty: z.string().optional(),
  license_number: z.string().optional(),
}).refine((d) => d.password === d.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
})

type FormValues = z.infer<typeof schema>

const ROLES = [
  { value: 'patient' as const, label: 'Patient', icon: User },
  { value: 'doctor' as const, label: 'Doctor', icon: Stethoscope },
  { value: 'admin' as const, label: 'Admin', icon: Shield },
]

const DASHBOARD: Record<string, string> = {
  patient: '/dashboard/patient',
  doctor: '/dashboard/doctor',
  admin: '/dashboard/admin',
}

export default function RegisterPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [serverError, setServerError] = useState('')

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { role: 'patient' },
  })

  const selectedRole = watch('role')

  const onSubmit = async (values: FormValues) => {
    setServerError('')
    try {
      const { token, user } = await authApi.register({
        email: values.email,
        password: values.password,
        full_name: values.full_name,
        role: values.role,
      })
      login(token, user)
      router.push(DASHBOARD[user.role] ?? '/dashboard/patient')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Registration failed. Please try again.'
      setServerError(msg)
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Create account</h1>
      <p className="text-sm text-gray-500 mb-6">Join SwasthyaAI to get started</p>

      {/* Role selector */}
      <div className="grid grid-cols-3 gap-2 mb-6">
        {ROLES.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            type="button"
            onClick={() => setValue('role', value)}
            className={`flex flex-col items-center gap-1 p-3 rounded-xl border-2 text-sm transition-all ${
              selectedRole === value
                ? 'border-teal-600 bg-teal-50 text-teal-700'
                : 'border-gray-200 text-gray-500 hover:border-gray-300'
            }`}
          >
            <Icon className="w-5 h-5" />
            <span className="font-medium">{label}</span>
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Full name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Full name</label>
          <input
            {...register('full_name')}
            type="text"
            placeholder="Dr. Jane Smith"
            className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
          />
          {errors.full_name && <p className="text-xs text-red-500 mt-1">{errors.full_name.message}</p>}
        </div>

        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            {...register('email')}
            type="email"
            placeholder="you@hospital.org"
            className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
          />
          {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
        </div>

        {/* Password */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <div className="relative">
            <input
              {...register('password')}
              type={showPassword ? 'text' : 'password'}
              placeholder="Min 8 chars, one number"
              className="w-full px-3 py-2 pr-10 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
        </div>

        {/* Confirm password */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Confirm password</label>
          <input
            {...register('confirm_password')}
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            className="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
          />
          {errors.confirm_password && (
            <p className="text-xs text-red-500 mt-1">{errors.confirm_password.message}</p>
          )}
        </div>

        {/* Patient-specific fields */}
        {selectedRole === 'patient' && (
          <div className="grid grid-cols-2 gap-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Date of birth</label>
              <input
                {...register('date_of_birth')}
                type="date"
                className="w-full px-2 py-1.5 rounded-md border border-gray-300 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Blood group</label>
              <select
                {...register('blood_group')}
                className="w-full px-2 py-1.5 rounded-md border border-gray-300 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
              >
                <option value="">Select</option>
                {BLOOD_GROUPS.map((g) => <option key={g}>{g}</option>)}
              </select>
            </div>
          </div>
        )}

        {/* Doctor-specific fields */}
        {selectedRole === 'doctor' && (
          <div className="grid grid-cols-2 gap-3 p-3 bg-green-50 rounded-lg border border-green-100">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Specialty</label>
              <select
                {...register('specialty')}
                className="w-full px-2 py-1.5 rounded-md border border-gray-300 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
              >
                <option value="">Select specialty</option>
                {SPECIALTIES.map((s) => <option key={s}>{s}</option>)}
              </select>
              {errors.specialty && <p className="text-xs text-red-500 mt-1">{errors.specialty.message}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">License number</label>
              <input
                {...register('license_number')}
                type="text"
                placeholder="MCI-12345"
                className="w-full px-2 py-1.5 rounded-md border border-gray-300 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>
        )}

        {/* Server error */}
        {serverError && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-600">
            {serverError}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-2.5 rounded-lg bg-teal-600 text-white font-medium text-sm hover:bg-teal-700 disabled:opacity-60 transition-colors flex items-center justify-center gap-2"
        >
          {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
          Create account
        </button>
      </form>

      <p className="text-center text-sm text-gray-500 mt-6">
        Already have an account?{' '}
        <Link href="/login" className="text-teal-600 font-medium hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  )
}
