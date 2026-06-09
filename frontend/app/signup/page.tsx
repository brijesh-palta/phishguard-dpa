'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Alert } from '@/components/ui/Alert'
import { auth, db } from '@/lib/firebase'
import {
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
} from 'firebase/auth'
import { setDoc, doc } from 'firebase/firestore'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/hooks'
import { useEffect } from 'react'

interface SignupForm {
  email: string
  password: string
  confirmPassword: string
}

export default function SignupPage() {
  const router = useRouter()
  const { user, loading } = useAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    if (user && !loading) {
      router.push('/dashboard')
    }
  }, [user, loading, router])

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<SignupForm>()

  const password = watch('password')

  const handleEmailSignup = async (data: SignupForm) => {
    setIsLoading(true)
    setError(null)

    try {
      const userCredential = await createUserWithEmailAndPassword(auth, data.email, data.password)
      await setDoc(doc(db, 'users', userCredential.user.uid), {
        email: data.email,
        createdAt: new Date().toISOString(),
      })
      console.log('signup success:', userCredential)
      setSuccess('Account created successfully â€” redirecting...')
      setError(null)
      // give user a short confirmation moment before redirect
      setTimeout(() => router.push('/dashboard'), 1200)
    } catch (err: any) {
      console.error('signup error', err)
      setError(err.message || 'Failed to create account')
      setSuccess(null)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleSignup = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const provider = new GoogleAuthProvider()
      const userCredential = await signInWithPopup(auth, provider)
      await setDoc(doc(db, 'users', userCredential.user.uid), {
        email: userCredential.user.email,
        createdAt: new Date().toISOString(),
      }, { merge: true })
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Failed to sign up with Google')
    } finally {
      setIsLoading(false)
    }
  }

  if (loading) return null

  return (
    <div className="min-h-screen grid place-items-center bg-gradient-to-br from-slate-100 via-white to-slate-100 text-slate-900 px-4">
      <div className="w-full max-w-6xl rounded-[2rem] bg-white shadow-[0_40px_120px_rgba(15,23,42,0.08)] overflow-hidden ring-1 ring-slate-200">
        <div className="relative grid gap-8 md:grid-cols-[0.95fr_1.05fr]">
          <div className="relative overflow-hidden bg-orange-500 text-white p-10 md:p-12">
            <div className="absolute -right-16 top-8 h-48 w-48 rounded-full bg-white/15 blur-3xl" />
            <div className="absolute -left-16 bottom-10 h-44 w-44 rounded-full bg-white/10" />
            <div className="relative z-10 flex h-full flex-col justify-between">
              <div>
                <span className="inline-flex rounded-full bg-white/15 px-4 py-1 text-xs uppercase tracking-[0.25em] text-white/90">Welcome</span>
                <h1 className="mt-8 text-4xl font-semibold leading-tight">Secure your account</h1>
                <p className="mt-4 max-w-sm text-sm leading-6 text-orange-100/90">
                  Join the community of security-conscious teams and protect your inbox with AI-driven phishing detection.
                </p>
              </div>

              <div className="mt-10 space-y-4">
                <div className="rounded-3xl bg-white/10 p-4 backdrop-blur">
                  <p className="text-sm text-orange-100">Fast onboarding</p>
                </div>
                <div className="rounded-3xl bg-white/10 p-4 backdrop-blur">
                  <p className="text-sm text-orange-100">Secure access</p>
                </div>
              </div>
            </div>
          </div>

          <div className="p-8 md:p-10">
            <div className="mb-8 text-center">
              <span className="inline-flex rounded-full bg-slate-100 px-4 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-slate-600">Create account</span>
              <h2 className="mt-5 text-3xl font-semibold text-slate-900">Start securing your inbox</h2>
              <p className="mt-3 text-sm text-slate-500">Fill in your details to create an account and get instant protection.</p>
            </div>

            {success && <Alert variant="success">{success}</Alert>}
            {error && <Alert variant="error">{error}</Alert>}

            <form onSubmit={handleSubmit(handleEmailSignup)} className="space-y-5">
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
                placeholder="Create a password"
                fullWidth
                {...register('password', {
                  required: 'Password is required',
                  minLength: { value: 6, message: 'Password must be at least 6 characters' },
                })}
                error={errors.password?.message}
              />

              <Input
                label="Confirm password"
                type="password"
                placeholder="Repeat your password"
                fullWidth
                {...register('confirmPassword', {
                  required: 'Please confirm your password',
                  validate: (value) => value === password || 'Passwords do not match',
                })}
                error={errors.confirmPassword?.message}
              />

              <Button type="submit" fullWidth isLoading={isLoading} className="w-full bg-orange-600 text-white hover:bg-orange-700 border-0 shadow-sm font-semibold">
                Create Account
              </Button>
            </form>

            <div className="mt-6 flex items-center gap-3 text-sm text-slate-500">
              <span className="h-px flex-1 bg-slate-200"></span>
              <span>or sign up with</span>
              <span className="h-px flex-1 bg-slate-200"></span>
            </div>

            <Button onClick={handleGoogleSignup} variant="ghost" fullWidth className="mt-5 w-full border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 flex items-center justify-center gap-3">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-slate-100">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="18" height="18"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C34.7 32.9 30 36 24 36c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.3 0 6.3 1.2 8.6 3.2l6-6C34.9 3.6 29.8 1.5 24 1.5 12 1.5 2.5 11 2.5 23S12 44.5 24 44.5c11.3 0 20.6-8 20.6-21 0-1.4-.1-2.5-.9-2.9z"/><path fill="#FF3D00" d="M6.3 14.2l6.6 4.8C14.9 15 19 12 24 12c3.3 0 6.3 1.2 8.6 3.2l6-6C34.9 3.6 29.8 1.5 24 1.5 16.3 1.5 9.6 5.7 6.3 14.2z"/><path fill="#4CAF50" d="M24 44.5c6 0 10.7-3.1 13.8-7.9L31.5 30.6C29.3 33 26.7 34.5 24 34.5c-6 0-10.7-3.1-13.8-7.9L6.3 30.8C9.6 39.3 16.3 44.5 24 44.5z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-1.1 3-3.4 5.5-6.3 6.9l9.6 7.2C40.9 36.9 45 29.5 45 23c0-1.4-.1-2.5-.9-2.9z"/></svg>
              </span>
              Continue with Google
            </Button>

            <p className="mt-7 text-center text-sm text-slate-500">
              Already have an account?{' '}
              <Link href="/login" className="font-semibold text-slate-900 hover:text-orange-600">Login</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
