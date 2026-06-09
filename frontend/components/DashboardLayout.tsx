'use client'

import { useAuth } from '@/lib/hooks'
import { Sidebar } from './Sidebar'
import { useUIStore } from '@/lib/store'

export function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, loading } = useAuth()
  const { sidebarOpen, setSidebarOpen } = useUIStore()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-300 border-t-black rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 md:ml-0 pt-16 md:pt-0">
        {children}
      </main>
    </div>
  )
}
