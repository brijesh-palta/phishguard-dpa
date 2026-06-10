'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { DashboardLayout } from '@/components/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Alert } from '@/components/ui/Alert'
import { detectionAPI, TrainingChallengeRequest, TrainingChallengeResponse } from '@/lib/api'
import { useAuth } from '@/lib/hooks'
import { db } from '@/lib/firebase'
import { collection, addDoc } from 'firebase/firestore'

const SCENARIO_OPTIONS = [
  { label: 'Password Reset Drill', value: 'password_reset' },
  { label: 'Invoice Review Exercise', value: 'invoice' },
  { label: 'HR Policy Simulation', value: 'hr_policy' },
  { label: 'Cloud Share Awareness', value: 'cloud_storage' },
]

const DIFFICULTY_OPTIONS = [
  { label: 'Easy', value: 'easy' },
  { label: 'Medium', value: 'medium' },
  { label: 'Hard', value: 'hard' },
]

interface SimulationForm {
  scenario: string
  difficulty: 'easy' | 'medium' | 'hard'
  employee_name: string
  company_name: string
  base_url: string
}

export default function SimulationPage() {
  const { user } = useAuth()
  const [challenge, setChallenge] = useState<TrainingChallengeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SimulationForm>({
    defaultValues: {
      scenario: 'password_reset',
      difficulty: 'medium',
      employee_name: 'Alex',
      company_name: 'Acme Corp',
      base_url: typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000',
    },
  })

  const onSubmit = async (data: SimulationForm) => {
    setLoading(true)
    setError(null)
    setChallenge(null)

    try {
      const payload: TrainingChallengeRequest = {
        scenario: data.scenario,
        difficulty: data.difficulty,
        employee_name: data.employee_name,
        company_name: data.company_name,
        base_url: data.base_url,
      }
      const response = await detectionAPI.generateTrainingChallenge(payload)
      setChallenge(response)
      if (user) {
        await addDoc(collection(db, 'users', user.uid, 'simulations'), {
          ...response,
          scenario: data.scenario,
          difficulty: data.difficulty,
          employee_name: data.employee_name,
          company_name: data.company_name,
          createdAt: new Date().toISOString(),
        })
      }
    } catch (err: any) {
      setError(err?.message || 'Unable to generate a training challenge. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Phishing Simulation Lab</h1>
          <p className="text-gray-600 max-w-3xl">
            Generate safe, creative phishing training scenarios for your team. Review red flags, practice reporting, and explore a polished awareness workflow.
          </p>
        </div>

        <div className="grid xl:grid-cols-[430px_1fr] gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Build Your Training Challenge</CardTitle>
            </CardHeader>
            <CardContent>
              {error && <Alert variant="error">{error}</Alert>}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                <div className="space-y-4">
                  <label className="block text-sm font-medium text-gray-700">Scenario</label>
                  <select
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg text-black focus:outline-none focus:ring-2 focus:ring-black"
                    {...register('scenario', { required: true })}
                  >
                    {SCENARIO_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-4">
                  <label className="block text-sm font-medium text-gray-700">Difficulty</label>
                  <select
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg text-black focus:outline-none focus:ring-2 focus:ring-black"
                    {...register('difficulty', { required: true })}
                  >
                    {DIFFICULTY_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <Input
                  label="Employee Name"
                  placeholder="Alex"
                  fullWidth
                  {...register('employee_name', { required: 'Employee name is required' })}
                  error={errors.employee_name?.message}
                />
                <Input
                  label="Company Name"
                  placeholder="Acme Corp"
                  fullWidth
                  {...register('company_name', { required: 'Company name is required' })}
                  error={errors.company_name?.message}
                />
                <Input
                  label="Base URL"
                  placeholder="http://localhost:8000"
                  fullWidth
                  {...register('base_url', { required: 'Base URL is required' })}
                  error={errors.base_url?.message}
                />

                <Button type="submit" isLoading={loading} className="w-full" size="lg">
                  Generate Training Scenario
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="space-y-6">
            <CardHeader>
              <CardTitle>Scenario Preview</CardTitle>
            </CardHeader>
            <CardContent>
              {!challenge ? (
                <div className="text-gray-500 py-16 text-center">
                  <p className="text-xl">No challenge generated yet.</p>
                  <p className="mt-2">Choose a scenario and click the button to create your phishing simulation.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="rounded-2xl bg-slate-950 text-white p-5">
                    <div className="flex flex-col gap-3">
                      <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-300">
                        <span className="px-2 py-1 bg-slate-700 rounded-full">{challenge.scenario.replace('_', ' ').toUpperCase()}</span>
                        <span className="px-2 py-1 bg-slate-700 rounded-full">{challenge.difficulty}</span>
                        <span className="px-2 py-1 bg-slate-700 rounded-full">ID {challenge.tracking_id}</span>
                      </div>
                      <div>
                        <p className="text-sm text-slate-400">Subject</p>
                        <p className="text-xl font-semibold">{challenge.subject}</p>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div className="rounded-xl bg-slate-900 p-4">
                          <p className="text-xs uppercase tracking-wide text-slate-500">Points Available</p>
                          <div className="mt-3 space-y-2 text-sm text-slate-300">
                            <p>Report: {challenge.points_available.report}</p>
                            <p>Find red flags: {challenge.points_available.identify_all_red_flags}</p>
                            <p>Avoid click: {challenge.points_available.avoid_click}</p>
                          </div>
                        </div>
                        <div className="rounded-xl bg-slate-900 p-4">
                          <p className="text-xs uppercase tracking-wide text-slate-500">Hints</p>
                          <ul className="mt-3 space-y-2 text-sm text-slate-300 list-disc list-inside">
                            {challenge.hints.map((hint) => (
                              <li key={hint}>{hint}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <a
                      href={challenge.landing_page_url}
                      target="_blank"
                      rel="noreferrer"
                      className="block rounded-lg border border-black bg-black px-4 py-4 text-center text-white transition hover:bg-gray-900"
                    >
                      Open Training Link
                    </a>
                    <a
                      href={challenge.links[1]?.url}
                      target="_blank"
                      rel="noreferrer"
                      className="block rounded-lg border border-gray-200 bg-white px-4 py-4 text-center text-black transition hover:bg-gray-50"
                    >
                      View Awareness Tips
                    </a>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold">Red Flags</h3>
                      <ul className="mt-3 space-y-2 text-sm text-gray-700 list-disc list-inside">
                        {challenge.red_flags.map((flag) => (
                          <li key={flag}>{flag}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold">Training Email Copy</h3>
                      <pre className="max-h-56 overflow-auto rounded-lg bg-slate-950 p-4 text-sm text-slate-200">
                        {challenge.body}
                      </pre>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
                    <p className="text-sm font-semibold text-gray-700">Safety Note</p>
                    <p className="mt-2 text-sm text-gray-600">{challenge.safety_note}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
