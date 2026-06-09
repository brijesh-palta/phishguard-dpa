'use client'

import { DashboardLayout } from '@/components/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Alert } from '@/components/ui/Alert'
import { useAuth } from '@/lib/hooks'
import { auth } from '@/lib/firebase'
import { signOut, updatePassword, EmailAuthProvider, reauthenticateWithCredential } from 'firebase/auth'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Input } from '@/components/ui/Input'
import { useRouter } from 'next/navigation'

interface PasswordForm {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

export default function ProfilePage() {
  const { user } = useAuth()
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<PasswordForm>()

  const newPassword = watch('newPassword')

  const handlePasswordChange = async (data: PasswordForm) => {
    setIsLoading(true)
    setError(null)
    setSuccess(null)

    try {
      if (!auth.currentUser?.email) {
        throw new Error('User not found')
      }

      // Reauthenticate user
      const credential = EmailAuthProvider.credential(
        auth.currentUser.email,
        data.currentPassword
      )
      await reauthenticateWithCredential(auth.currentUser, credential)

      // Update password
      await updatePassword(auth.currentUser, data.newPassword)

      setSuccess('Password updated successfully')
      reset()
    } catch (err: any) {
      setError(err.message || 'Failed to update password')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSignOut = async () => {
    try {
      await signOut(auth)
      router.push('/')
    } catch (err) {
      console.error('Sign out failed:', err)
    }
  }

  return (
    <DashboardLayout>
      <div className="p-6 max-w-2xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Profile</h1>
          <p className="text-gray-600">Manage your account settings</p>
        </div>

        {/* Account Info */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Email Address</p>
              <p className="font-semibold">{user?.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Account Created</p>
              <p className="font-semibold">
                {user?.metadata?.creationTime
                  ? new Date(user.metadata.creationTime).toLocaleDateString()
                  : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Last Sign In</p>
              <p className="font-semibold">
                {user?.metadata?.lastSignInTime
                  ? new Date(user.metadata.lastSignInTime).toLocaleDateString()
                  : 'N/A'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Change Password */}
        {user?.providerData[0]?.providerId === 'password' && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
            </CardHeader>
            <CardContent>
              {error && <Alert variant="error" className="mb-4">{error}</Alert>}
              {success && (
                <Alert variant="success" className="mb-4">{success}</Alert>
              )}

              <form
                onSubmit={handleSubmit(handlePasswordChange)}
                className="space-y-4"
              >
                <Input
                  label="Current Password"
                  type="password"
                  placeholder="••••••••"
                  fullWidth
                  {...register('currentPassword', {
                    required: 'Current password is required',
                  })}
                  error={errors.currentPassword?.message}
                />

                <Input
                  label="New Password"
                  type="password"
                  placeholder="••••••••"
                  fullWidth
                  {...register('newPassword', {
                    required: 'New password is required',
                    minLength: {
                      value: 6,
                      message: 'Password must be at least 6 characters',
                    },
                  })}
                  error={errors.newPassword?.message}
                />

                <Input
                  label="Confirm New Password"
                  type="password"
                  placeholder="••••••••"
                  fullWidth
                  {...register('confirmPassword', {
                    required: 'Please confirm your password',
                    validate: (value) =>
                      value === newPassword || 'Passwords do not match',
                  })}
                  error={errors.confirmPassword?.message}
                />

                <Button type="submit" isLoading={isLoading} className="w-full">
                  Update Password
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Sign Out */}
        <Card>
          <CardHeader>
            <CardTitle>Session</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4">
              Sign out of your account on this device
            </p>
            <Button variant="danger" onClick={handleSignOut} className="w-full">
              Sign Out
            </Button>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
