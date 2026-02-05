'use client'

import { useEffect, useState } from 'react'

export default function Header() {
  const [isOnline, setIsOnline] = useState(true)
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking')

  // Check browser online/offline status
  useEffect(() => {
    const updateOnlineStatus = () => {
      setIsOnline(navigator.onLine)
    }

    window.addEventListener('online', updateOnlineStatus)
    window.addEventListener('offline', updateOnlineStatus)

    updateOnlineStatus()

    return () => {
      window.removeEventListener('online', updateOnlineStatus)
      window.removeEventListener('offline', updateOnlineStatus)
    }
  }, [])

  // Check backend health
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/health', {
          method: 'GET',
          signal: AbortSignal.timeout(3000) // 3 second timeout
        })

        if (response.ok) {
          setBackendStatus('online')
        } else {
          setBackendStatus('offline')
        }
      } catch (error) {
        setBackendStatus('offline')
      }
    }

    checkBackend()

    // Re-check every 30 seconds
    const interval = setInterval(checkBackend, 30000)

    return () => clearInterval(interval)
  }, [])

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Page Title (can be dynamic based on route) */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Welcome</h2>
          <p className="text-sm text-gray-500">Offline-First Hospital AI System</p>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center space-x-4">
          {/* Network Status */}
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm font-medium text-gray-700">
              {isOnline ? 'Network Online' : 'Network Offline'}
            </span>
          </div>

          {/* Backend Status */}
          <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-100">
            {backendStatus === 'checking' && (
              <>
                <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
                <span className="text-sm font-medium text-gray-700">Checking...</span>
              </>
            )}
            {backendStatus === 'online' && (
              <>
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-sm font-medium text-gray-700">Backend Ready</span>
              </>
            )}
            {backendStatus === 'offline' && (
              <>
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-sm font-medium text-gray-700">Backend Offline</span>
              </>
            )}
          </div>

          {/* User Menu (placeholder) */}
          <div className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 px-3 py-2 rounded-lg">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
              U
            </div>
            <span className="text-sm font-medium text-gray-700">User</span>
          </div>
        </div>
      </div>
    </header>
  )
}
