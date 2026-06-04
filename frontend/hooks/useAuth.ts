'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'

const TOKEN_KEY = 'swasthya_token'

/** Mirror the JWT into a cookie so the SSR middleware (which can't read
 *  localStorage) can authenticate route requests. Not httpOnly by necessity
 *  (set from JS), but scoped + lax to limit exposure. */
function setTokenCookie(token: string) {
  if (typeof document === 'undefined') return
  const maxAge = 60 * 60 * 24 // 24h, matches backend JWT_EXPIRE_MINUTES
  const secure = typeof location !== 'undefined' && location.protocol === 'https:' ? '; Secure' : ''
  document.cookie = `${TOKEN_KEY}=${token}; Path=/; Max-Age=${maxAge}; SameSite=Lax${secure}`
}

function clearTokenCookie() {
  if (typeof document === 'undefined') return
  document.cookie = `${TOKEN_KEY}=; Path=/; Max-Age=0; SameSite=Lax`
}

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
          setTokenCookie(token)
        }
        set({ user, token, isAuthenticated: true })
      },

      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem(TOKEN_KEY)
          clearTokenCookie()
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
      // Re-mirror the persisted token into the cookie on reload so SSR
      // middleware keeps working across refreshes.
      onRehydrateStorage: () => (state) => {
        if (state?.token) setTokenCookie(state.token)
      },
    }
  )
)
