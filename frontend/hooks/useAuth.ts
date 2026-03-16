'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'

const TOKEN_KEY = 'swasthya_token'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
  isDoctor: () => boolean
  isPatient: () => boolean
  isAdmin: () => boolean
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: (token: string, user: User) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem(TOKEN_KEY, token)
        }
        set({ user, token, isAuthenticated: true })
      },

      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem(TOKEN_KEY)
        }
        set({ user: null, token: null, isAuthenticated: false })
      },

      isDoctor: () => get().user?.role === 'doctor',
      isPatient: () => get().user?.role === 'patient',
      isAdmin: () => get().user?.role === 'admin',
    }),
    {
      name: 'swasthya-auth',
      partialize: (state) => ({ user: state.user, token: state.token, isAuthenticated: state.isAuthenticated }),
    }
  )
)
