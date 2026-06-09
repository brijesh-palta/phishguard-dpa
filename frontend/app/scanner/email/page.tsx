'use client'

import { useState } from 'react'
import { DashboardLayout } from '@/components/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { detectionAPI, DetectionRequest } from '@/lib/api'
import { useForm } from 'react-hook-form'
import { useScanStore } from '@/lib/store'
import { db, auth } from '@/lib/firebase'
import { collection, addDoc } from 'firebase/firestore'

interface EmailScanForm
  extends Omit<DetectionRequest, 'urls' | 'image_urls' | 'attachment_names'> {
  urls: string
  image_urls?: string
  attachment_names?: string
}

export default function EmailScannerPage() {
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { addScan } = useScanStore()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<EmailScanForm>({
    defaultValues: {
      subject: 'Urgent password verification required',
      body: 'Your account will be suspended within 24 hours. Verify your password immediately to restore access.',
      urls: 'http://secure-login-support.xyz/verify',
      sender_email: 'security-alerts@company-support-reset.xyz',
      expected_domain: 'example.com',
    },
  })

  const onSubmit = async (data: EmailScanForm) => {
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      const payload: DetectionRequest = {
        subject: data.subject,
        body: data.body,
        html_body: data.html_body,
        urls: data.urls
          .split('\n')
          .map((u) => u.trim())
          .filter(Boolean),
        image_urls:
          data.image_urls
            ?.split('\n')
            .map((u) => u.trim())
            .filter(Boolean) || [],
        attachment_names:
          data.attachment_names
            ?.split('\n')
            .map((u) => u.trim())
            .filter(Boolean) || [],
        sender_email: data.sender_email,
        reply_to_email: data.reply_to_email,
        expected_domain: data.expected_domain,
      }

      const detectionResult = await detectionAPI.detectEmail(payload)
      setResult(detectionResult)

      // Save to Firestore
      if (auth.currentUser) {
        await addDoc(
          collection(db, 'users', auth.currentUser.uid, 'scans'),
          {
            type: 'email',
            subject: data.subject,
            payload,
            result: detectionResult,
            createdAt: new Date().toISOString(),
          }
        )
      }

      addScan({
        id: detectionResult.id,
        type: 'email',
        subject: data.subject,
        result: detectionResult,
        timestamp: new Date().toISOString(),
      })
    } catch (err: any) {
      setError(err.message || 'Failed to analyze email')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="p-6 max-w-6xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Email Scanner</h1>
          <p className="text-gray-600">
            Analyze email content for phishing threats and security risks
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <Card>
            <CardHeader>
              <CardTitle>Scan Email</CardTitle>
            </CardHeader>
            <CardContent>
              {error && <Alert variant="error" className="mb-4">{error}</Alert>}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <Input
                  label="Subject Line"
                  placeholder="Email subject..."
                  fullWidth
                  {...register('subject', { required: 'Subject is required' })}
                  error={errors.subject?.message}
                />

                <Textarea
                  label="Email Body"
                  placeholder="Paste the email text here..."
                  rows={4}
                  fullWidth
                  {...register('body', { required: 'Email body is required' })}
                  error={errors.body?.message}
                />

                <Textarea
                  label="HTML Body (Optional)"
                  placeholder="Paste HTML email content here..."
                  rows={3}
                  fullWidth
                  {...register('html_body')}
                />

                <Input
                  label="Sender Email"
                  type="email"
                  placeholder="sender@domain.com"
                  fullWidth
                  {...register('sender_email')}
                />

                <Input
                  label="Reply-To Email (Optional)"
                  type="email"
                  placeholder="reply@domain.com"
                  fullWidth
                  {...register('reply_to_email')}
                />

                <Input
                  label="Expected Company Domain"
                  placeholder="company.com"
                  fullWidth
                  {...register('expected_domain')}
                />

                <Textarea
                  label="URLs (One per line)"
                  placeholder="http://example.com"
                  rows={2}
                  fullWidth
                  {...register('urls')}
                />

                <Textarea
                  label="Image URLs (One per line, Optional)"
                  placeholder="https://example.com/image.gif"
                  rows={2}
                  fullWidth
                  {...register('image_urls')}
                />

                <Textarea
                  label="Attachment Names (One per line, Optional)"
                  placeholder="invoice.pdf"
                  rows={2}
                  fullWidth
                  {...register('attachment_names')}
                />

                <Button
                  type="submit"
                  isLoading={isLoading}
                  className="w-full"
                  size="lg"
                >
                  Analyze Email
                </Button>
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
                  <div className="text-4xl mb-4">📊</div>
                  <p>Submit an email to see analysis results</p>
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
                  <div className="space-y-3">
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm font-semibold mb-2">
                        Content Risk: {(result.content_probability * 100).toFixed(0)}%
                      </p>
                      {result.reasons && (
                        <ul className="text-xs space-y-1">
                          {result.reasons.map((r: string, i: number) => (
                            <li key={i}>• {r}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {result.sender_analysis && (
                      <div className="p-3 bg-yellow-50 rounded-lg">
                        <p className="text-sm font-semibold mb-2">
                          Sender Analysis ({result.sender_analysis.risk_score}/100)
                        </p>
                        <p className="text-xs font-medium mb-1">
                          Verdict: {result.sender_analysis.verdict}
                        </p>
                        <ul className="text-xs space-y-1">
                          {result.sender_analysis.findings?.map(
                            (f: string, i: number) => (
                              <li key={i}>• {f}</li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                    {result.structure_analysis && (
                      <div className="p-3 bg-red-50 rounded-lg">
                        <p className="text-sm font-semibold mb-2">
                          Structure Analysis ({result.structure_analysis.risk_score}/100)
                        </p>
                        <p className="text-xs font-medium mb-1">
                          Verdict: {result.structure_analysis.verdict}
                        </p>
                        <ul className="text-xs space-y-1">
                          {result.structure_analysis.findings?.map(
                            (f: string, i: number) => (
                              <li key={i}>• {f}</li>
                            )
                          )}
                        </ul>
                      </div>
                    )}
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full"
                    onClick={() => reset()}
                  >
                    Clear
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
