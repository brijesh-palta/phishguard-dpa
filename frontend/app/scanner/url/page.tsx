'use client'

import { useState } from 'react'
import { DashboardLayout } from '@/components/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { detectionAPI, DetectionRequest } from '@/lib/api'
import { useForm } from 'react-hook-form'
import { useScanStore } from '@/lib/store'
import { db, auth } from '@/lib/firebase'
import { collection, addDoc } from 'firebase/firestore'

interface URLScanForm {
  url: string
}

export default function URLScannerPage() {
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { addScan } = useScanStore()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<URLScanForm>({
    defaultValues: {
      url: 'http://secure-login-support.xyz/verify',
    },
  })

  const onSubmit = async (data: URLScanForm) => {
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const payload: DetectionRequest = {
        subject: `URL Analysis: ${data.url}`,
        body: `Scanning URL for security threats: ${data.url}`,
        urls: [data.url],
      }

      const detectionResult = await detectionAPI.detectEmail(payload)
      setResult(detectionResult)

      // Save to Firestore
      if (auth.currentUser) {
        await addDoc(
          collection(db, 'users', auth.currentUser.uid, 'scans'),
          {
            type: 'url',
            url: data.url,
            payload,
            result: detectionResult,
            createdAt: new Date().toISOString(),
          }
        )
      }

      addScan({
        id: detectionResult.id,
        type: 'url',
        url: data.url,
        result: detectionResult,
        timestamp: new Date().toISOString(),
      })
    } catch (err: any) {
      setError(err.message || 'Failed to analyze URL')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="p-6 max-w-4xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">URL Scanner</h1>
          <p className="text-gray-600">
            Check if a link is safe or potentially malicious
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <Card>
            <CardHeader>
              <CardTitle>Check URL</CardTitle>
            </CardHeader>
            <CardContent>
              {error && <Alert variant="error" className="mb-4">{error}</Alert>}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <Input
                  label="Enter URL"
                  type="url"
                  placeholder="https://example.com"
                  fullWidth
                  {...register('url', {
                    required: 'URL is required',
                    pattern: {
                      value:
                        /^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
                      message: 'Please enter a valid URL',
                    },
                  })}
                  error={errors.url?.message}
                />

                <Button
                  type="submit"
                  isLoading={isLoading}
                  className="w-full"
                  size="lg"
                >
                  Scan URL
                </Button>

                {/* Examples */}
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <p className="text-sm font-semibold mb-3">Try these examples:</p>
                  <div className="space-y-2">
                    {[
                      'https://www.google.com',
                      'https://suspicious-login.xyz',
                      'https://amazon.com',
                    ].map((example) => (
                      <button
                        key={example}
                        onClick={() => {
                          reset({ url: example })
                        }}
                        className="block w-full text-left text-sm px-3 py-2 rounded border border-gray-200 hover:bg-gray-50 transition-colors"
                      >
                        {example}
                      </button>
                    ))}
                  </div>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Results Panel */}
          <Card className="sticky top-6 h-fit">
            <CardHeader>
              <CardTitle>Analysis Result</CardTitle>
            </CardHeader>
            <CardContent>
              {!result ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">🔍</div>
                  <p>Enter a URL to see analysis results</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Risk Badge */}
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">Verdict:</span>
                    <Badge
                      label={result.label?.toUpperCase()}
                      variant={
                        result.label === 'phishing' ? 'phishing' : 'safe'
                      }
                    />
                  </div>

                  {/* Risk Level */}
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">Risk Level</p>
                    <p className="text-lg font-bold mt-1">
                      {result.risk_level}
                    </p>
                  </div>

                  {/* Confidence */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-600">Confidence</p>
                      <p className="text-lg font-bold mt-1">
                        {(result.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-600">Phishing Prob.</p>
                      <p className="text-lg font-bold mt-1">
                        {(result.phishing_probability * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  {/* Analysis Breakdown */}
                  {result.reasons && result.reasons.length > 0 && (
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm font-semibold mb-2">
                        Detection Reasons
                      </p>
                      <ul className="text-xs space-y-1">
                        {result.reasons.map((r: string, i: number) => (
                          <li key={i}>• {r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full"
                    onClick={() => reset()}
                  >
                    Scan Another
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
