'use client'

import { useEffect, useState } from 'react'
import { useAuthStore } from './store'
import { auth } from './firebase'
import { onAuthStateChanged } from 'firebase/auth'

export function useAuth() {
  const { user, loading, setUser, setLoading } = useAuthStore()
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    if (!auth) {
      setUser(null)
      setLoading(false)
      setInitialized(true)
      return
    }

    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser)
      setLoading(false)
      setInitialized(true)
    })

    return () => {
      if (typeof unsubscribe === 'function') unsubscribe()
    }
  }, [setUser, setLoading])

  return { user, loading: loading && !initialized }
}

export function isValidEmail(email: string): boolean {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return regex.test(email)
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d)
}

export function getRiskColor(score: number): string {
  if (score >= 75) return 'text-red-600'
  if (score >= 45) return 'text-yellow-600'
  return 'text-green-600'
}

export function getRiskBgColor(score: number): string {
  if (score >= 75) return 'bg-red-50'
  if (score >= 45) return 'bg-yellow-50'
  return 'bg-green-50'
}
