'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Alert } from '@/components/ui/Alert'
import { auth } from '@/lib/firebase'
import {
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
} from 'firebase/auth'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/hooks'
import { useEffect } from 'react'

interface LoginForm {
  email: string
  password: string
}

export default function LoginPage() {
  const router = useRouter()
  const { user, loading } = useAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (user && !loading) {
      router.push('/dashboard')
    }
  }, [user, loading, router])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>()

  const handleEmailLogin = async (data: LoginForm) => {
    setIsLoading(true)
    setError(null)

    try {
      await signInWithEmailAndPassword(auth, data.email, data.password)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Failed to sign in')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const provider = new GoogleAuthProvider()
      await signInWithPopup(auth, provider)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Failed to sign in with Google')
    } finally {
      setIsLoading(false)
    }
  }

  if (loading) return null

  return (
    <div className="min-h-screen grid place-items-center bg-gradient-to-br from-slate-100 via-white to-slate-100 text-slate-900 px-4">
      <div className="w-full max-w-6xl rounded-[2rem] bg-white shadow-[0_40px_120px_rgba(15,23,42,0.08)] overflow-hidden ring-1 ring-slate-200">
        <div className="relative grid gap-8 md:grid-cols-[1.1fr_0.9fr]">
          <div className="relative overflow-hidden bg-slate-900 text-white p-10 md:p-12">
            <div className="absolute -right-16 top-8 h-48 w-48 rounded-full bg-orange-400 opacity-20 blur-3xl" />
            <div className="absolute left-10 top-24 h-24 w-24 rounded-full border border-white/20 opacity-50" />
            <div className="absolute -bottom-12 left-16 h-40 w-40 rounded-full bg-slate-700/30 blur-2xl" />

            <div className="relative z-10 flex h-full flex-col justify-between">
              <div>
                <div className="inline-flex items-center gap-3 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white shadow-sm shadow-slate-900/10">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-300" /> Trusted Security
                </div>
                <h1 className="mt-10 text-4xl font-semibold leading-tight">Welcome back</h1>
                <p className="mt-4 max-w-md text-sm leading-6 text-slate-300">
                  Secure your inbox with intelligent phishing protection. Sign in and keep your team safe with instant risk scanning and history tracking.
                </p>
              </div>

              <div className="mt-10 space-y-4">
                <div className="rounded-3xl border border-white/10 bg-white/5 p-4 backdrop-blur">
                  <p className="text-sm text-slate-300">Instant phishing alerts</p>
                </div>
                <div className="rounded-3xl border border-white/10 bg-white/5 p-4 backdrop-blur">
                  <p className="text-sm text-slate-300">Secure dashboard access</p>
                </div>
              </div>
            </div>
          </div>

          <div className="p-8 md:p-10">
            <div className="mb-8 text-center">
              <span className="inline-flex rounded-full bg-orange-100 px-4 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-orange-700">Sign in</span>
              <h2 className="mt-5 text-3xl font-semibold text-slate-900">Access your account</h2>
              <p className="mt-3 text-sm text-slate-500">Enter your credentials to securely login and continue monitoring phishing threats.</p>
            </div>

            {error && <Alert variant="error">{error}</Alert>}

            <form onSubmit={handleSubmit(handleEmailLogin)} className="space-y-5">
              <Input
                label="Email address"
                type="email"
                placeholder="your@email.com"
                fullWidth
                {...register('email', {
                  required: 'Email is required',
                  pattern: {
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: 'Enter a valid email',
                  },
                })}
                error={errors.email?.message}
              />

              <Input
                label="Password"
                type="password"
                placeholder="Enter your password"
                fullWidth
                {...register('password', {
                  required: 'Password is required',
                  minLength: { value: 6, message: 'Password must be at least 6 characters' },
                })}
                error={errors.password?.message}
              />

              <Button type="submit" fullWidth isLoading={isLoading} className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white shadow-lg shadow-orange-200/30 hover:opacity-95">
                Sign In
              </Button>
            </form>

            <div className="mt-6 flex items-center gap-3 text-sm text-slate-500">
              <span className="h-px flex-1 bg-slate-200"></span>
              <span>or continue with</span>
              <span className="h-px flex-1 bg-slate-200"></span>
            </div>

            <Button onClick={handleGoogleLogin} variant="ghost" fullWidth className="mt-5 w-full border border-slate-200 bg-white text-slate-700 hover:bg-slate-50">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-slate-100">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="18" height="18"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C34.7 32.9 30 36 24 36c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.3 0 6.3 1.2 8.6 3.2l6-6C34.9 3.6 29.8 1.5 24 1.5 12 1.5 2.5 11 2.5 23S12 44.5 24 44.5c11.3 0 20.6-8 20.6-21 0-1.4-.1-2.5-.9-2.9z"/><path fill="#FF3D00" d="M6.3 14.2l6.6 4.8C14.9 15 19 12 24 12c3.3 0 6.3 1.2 8.6 3.2l6-6C34.9 3.6 29.8 1.5 24 1.5 16.3 1.5 9.6 5.7 6.3 14.2z"/><path fill="#4CAF50" d="M24 44.5c6 0 10.7-3.1 13.8-7.9L31.5 30.6C29.3 33 26.7 34.5 24 34.5c-6 0-10.7-3.1-13.8-7.9L6.3 30.8C9.6 39.3 16.3 44.5 24 44.5z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-1.1 3-3.4 5.5-6.3 6.9l9.6 7.2C40.9 36.9 45 29.5 45 23c0-1.4-.1-2.5-.9-2.9z"/></svg>
              </span>
              Continue with Google
            </Button>

            <p className="mt-7 text-center text-sm text-slate-500">
              Don’t have an account?{' '}
              <Link href="/signup" className="font-semibold text-slate-900 hover:text-orange-600">
                Create one
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
