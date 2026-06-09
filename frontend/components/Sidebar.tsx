'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/lib/hooks'
import { Button } from './ui/Button'
import { useUIStore } from '@/lib/store'
import { auth } from '@/lib/firebase'
import { signOut } from 'firebase/auth'

export function Sidebar() {
  const { user } = useAuth()
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const [isSigningOut, setIsSigningOut] = useState(false)

  const handleSignOut = async () => {
    setIsSigningOut(true)
    try {
      await signOut(auth)
    } catch (error) {
      console.error('Sign out failed:', error)
    } finally {
      setIsSigningOut(false)
    }
  }

  if (!user) return null

  const navItems = [
    { label: 'Dashboard', href: '/dashboard', icon: '📊' },
    { label: 'Email Scanner', href: '/scanner/email', icon: '📧' },
    { label: 'URL Scanner', href: '/scanner/url', icon: '🔗' },
    { label: 'Simulation Lab', href: '/dashboard/simulation', icon: '🎯' },
    { label: 'Scan History', href: '/history', icon: '📜' },
    { label: 'Profile', href: '/profile', icon: '👤' },
  ]

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={toggleSidebar}
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-black text-white rounded-lg"
      >
        ☰
      </button>

      {/* Sidebar overlay */}
      {sidebarOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => toggleSidebar()}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:sticky top-0 left-0 h-screen w-64 bg-black text-white border-r border-gray-800 flex flex-col z-40 transition-transform duration-300 ${
          !sidebarOpen ? '-translate-x-full md:translate-x-0' : ''
        }`}
      >
        {/* Logo */}
        <div className="px-6 py-8 border-b border-gray-800">
          <Link href="/dashboard" className="font-bold text-xl">
            PhishGuard
          </Link>
          <p className="text-xs text-gray-400 mt-1">Security Analyzer</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href}>
              <span className="block px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-900 hover:text-white transition-colors duration-200">
                <span className="mr-3">{item.icon}</span>
                {item.label}
              </span>
            </Link>
          ))}
        </nav>

        {/* User section */}
        <div className="px-4 py-4 border-t border-gray-800 space-y-3">
          <div className="px-4 py-3 bg-gray-900 rounded-lg">
            <p className="text-xs text-gray-400">Signed in as</p>
            <p className="text-sm font-medium text-white truncate">
              {user.email}
            </p>
          </div>
          <Button
            variant="ghost"
            size="md"
            fullWidth
            onClick={handleSignOut}
            isLoading={isSigningOut}
            className="text-white border-gray-700 hover:bg-gray-900 w-full"
          >
            Sign Out
          </Button>
        </div>
      </aside>
    </>
  )
}
