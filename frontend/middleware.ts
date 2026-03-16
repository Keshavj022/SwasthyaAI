import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PUBLIC_PATHS = ['/login', '/register']
const AUTH_PATHS = ['/login', '/register']

const DASHBOARD_BY_ROLE: Record<string, string> = {
  patient: '/dashboard/patient',
  doctor: '/dashboard/doctor',
  admin: '/dashboard/admin',
}

function getTokenFromCookieOrHeader(request: NextRequest): string | null {
  // Check cookie first (set by client code if needed)
  const cookie = request.cookies.get('swasthya_token')?.value
  if (cookie) return cookie
  // Check Authorization header
  const auth = request.headers.get('authorization')
  if (auth?.startsWith('Bearer ')) return auth.slice(7)
  return null
}

/**
 * Decode JWT payload without verification (verification is done on the backend).
 * We only need the role claim to redirect appropriately.
 */
function decodePayload(token: string): { sub?: string; role?: string; exp?: number } | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = parts[1]
    const padded = payload.padEnd(payload.length + ((4 - (payload.length % 4)) % 4), '=')
    return JSON.parse(atob(padded.replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return null
  }
}

function isExpired(payload: { exp?: number }): boolean {
  if (!payload.exp) return false
  return Date.now() / 1000 > payload.exp
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const isAuthPath = AUTH_PATHS.some((p) => pathname === p || pathname.startsWith(p + '/'))
  const isPublicPath = PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(p + '/'))
  const isDashboardPath = pathname.startsWith('/dashboard')
  const isRoot = pathname === '/'

  // Try to read token from Zustand persist storage via a cookie we can set from client
  // For SSR middleware, we rely on a cookie named 'swasthya_token'
  const token = getTokenFromCookieOrHeader(request)
  const payload = token ? decodePayload(token) : null
  const isAuthenticated = !!payload && !isExpired(payload)

  // Redirect unauthenticated users away from protected routes
  if ((isDashboardPath || isRoot) && !isAuthenticated) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Redirect authenticated users away from auth pages
  if (isAuthPath && isAuthenticated && payload?.role) {
    const dest = DASHBOARD_BY_ROLE[payload.role] ?? '/dashboard/patient'
    return NextResponse.redirect(new URL(dest, request.url))
  }

  // Redirect root to login (handled above if unauthenticated)
  if (isRoot && isAuthenticated && payload?.role) {
    return NextResponse.redirect(new URL(DASHBOARD_BY_ROLE[payload.role] ?? '/dashboard/patient', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/', '/login', '/register', '/dashboard/:path*'],
}
