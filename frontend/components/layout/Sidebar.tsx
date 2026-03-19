'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState } from 'react'
import {
  Home,
  MessageSquare,
  Calendar,
  FileText,
  FolderOpen,
  Pill,
  Target,
  Users,
  Stethoscope,
  ClipboardList,
  Microscope,
  LayoutDashboard,
  Settings,
  Activity,
  Menu,
  LogOut,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks/useAuth'
import { authApi } from '@/lib/api'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'

// ---------------------------------------------------------------------------
// Nav item definitions per role
// ---------------------------------------------------------------------------

interface NavItem {
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

const PATIENT_NAV: NavItem[] = [
  { label: 'Home', href: '/dashboard/patient', icon: Home },
  { label: 'Chat with AI', href: '/chat', icon: MessageSquare },
  { label: 'Appointments', href: '/appointments', icon: Calendar },
  { label: 'My Records', href: '/records', icon: ClipboardList },
  { label: 'Documents', href: '/documents', icon: FolderOpen },
  { label: 'Medications', href: '/medications', icon: Pill },
  { label: 'Health Goals', href: '/health-goals', icon: Target },
]

const DOCTOR_NAV: NavItem[] = [
  { label: 'Home', href: '/dashboard/doctor', icon: Home },
  { label: 'My Patients', href: '/patients', icon: Users },
  { label: 'AI Assistant', href: '/chat', icon: MessageSquare },
  { label: 'Schedule', href: '/schedule', icon: Calendar },
  { label: 'Consultations', href: '/consultations', icon: Stethoscope },
  { label: 'Diagnostics', href: '/diagnostics', icon: Microscope },
  { label: 'Documents', href: '/documents', icon: FolderOpen },
]

const ADMIN_NAV: NavItem[] = [
  { label: 'Home', href: '/dashboard/admin', icon: Home },
  { label: 'Users', href: '/admin/users', icon: Users },
  { label: 'Audit Logs', href: '/admin/audit', icon: FileText },
  { label: 'System Health', href: '/admin/system', icon: Activity },
  { label: 'All Appointments', href: '/admin/appointments', icon: Calendar },
  { label: 'Settings', href: '/admin/settings', icon: Settings },
]

const NAV_BY_ROLE: Record<string, NavItem[]> = {
  patient: PATIENT_NAV,
  doctor: DOCTOR_NAV,
  admin: ADMIN_NAV,
}

const ROLE_BADGE: Record<string, string> = {
  doctor: 'bg-teal-100 text-teal-700',
  patient: 'bg-blue-100 text-blue-700',
  admin: 'bg-red-100 text-red-700',
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((p) => p[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

// ---------------------------------------------------------------------------
// Nav list
// ---------------------------------------------------------------------------

function NavList({ items, pathname }: { items: NavItem[]; pathname: string }) {
  return (
    <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
      {items.map(({ label, href, icon: Icon }) => {
        const isActive = pathname === href || (href !== '/dashboard' && pathname.startsWith(href))
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
              isActive
                ? 'bg-white/15 text-white shadow-sm'
                : 'text-white/70 hover:bg-white/10 hover:text-white'
            )}
          >
            <Icon className={cn('w-4.5 h-4.5 shrink-0', isActive ? 'text-white' : 'text-white/60')} />
            <span>{label}</span>
            {isActive && <ChevronRight className="w-3.5 h-3.5 ml-auto text-white/50" />}
          </Link>
        )
      })}
    </nav>
  )
}

// ---------------------------------------------------------------------------
// User footer
// ---------------------------------------------------------------------------

function UserFooter({ onLogout }: { onLogout: () => void }) {
  const { user } = useAuth()
  if (!user) return null

  return (
    <div className="p-3 border-t border-white/10">
      <div className="flex items-center gap-3 px-2 py-2">
        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-white text-xs font-bold shrink-0">
          {getInitials(user.name)}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{user.name}</p>
          <span className={cn('text-[10px] font-semibold px-1.5 py-0.5 rounded-full', ROLE_BADGE[user.role] ?? 'bg-gray-100 text-gray-700')}>
            {user.role}
          </span>
        </div>
        <button
          onClick={onLogout}
          title="Logout"
          className="p-1.5 rounded-md text-white/50 hover:text-white hover:bg-white/10 transition-colors duration-150"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sidebar logo
// ---------------------------------------------------------------------------

function SidebarLogo() {
  return (
    <div className="px-4 py-5 border-b border-white/10">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
          <LayoutDashboard className="w-4 h-4 text-white" />
        </div>
        <div>
          <p className="text-white font-bold text-base leading-tight tracking-tight">
            Swasthya<span className="text-teal-300">AI</span>
          </p>
          <p className="text-white/40 text-[10px]">Offline-first</p>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Sidebar
// ---------------------------------------------------------------------------

function SidebarContent() {
  const pathname = usePathname()
  const router = useRouter()
  const { user } = useAuth()
  const items = NAV_BY_ROLE[user?.role ?? 'patient'] ?? PATIENT_NAV

  const handleLogout = () => {
    authApi.logout()
    router.push('/login')
  }

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-[#0F4C5C] to-[#0a3545]">
      <SidebarLogo />
      <NavList items={items} pathname={pathname} />
      <UserFooter onLogout={handleLogout} />
    </div>
  )
}

export default function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-60 shrink-0 flex-col h-screen sticky top-0">
        <SidebarContent />
      </aside>

      {/* Mobile hamburger trigger (rendered in Header via prop drilling) */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetTrigger asChild>
          <button
            id="sidebar-mobile-trigger"
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 text-gray-500"
            aria-label="Open navigation"
          >
            <Menu className="w-5 h-5" />
          </button>
        </SheetTrigger>
        <SheetContent side="left" className="w-60 p-0 border-0">
          <SidebarContent />
        </SheetContent>
      </Sheet>
    </>
  )
}
