'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/lib/hooks'
import { db } from '@/lib/firebase'
import { doc, getDoc, setDoc } from 'firebase/firestore'
import { DashboardLayout } from '@/components/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Alert } from '@/components/ui/Alert'
import { detectionAPI } from '@/lib/api'

interface CampaignPageProps {
  params: {
    campaignId: string
  }
}

function extractUrlsFromHtml(html: string): string[] {
  if (!html) return []
  const urlMatches = Array.from(html.matchAll(/href=["']([^"']+)["']/gi)).map((m) => m[1])
  return Array.from(new Set(urlMatches.filter(Boolean)))
}

function extractUrlsFromText(text: string): string[] {
  if (!text) return []
  const urlMatches = Array.from(text.matchAll(/https?:\/\/[\w\-\.\?\#\/%&=\+\-_,;:@]+/gi)).map((m) => m[0])
  return Array.from(new Set(urlMatches.filter(Boolean)))
}

export default function CampaignDetailsPage({ params }: CampaignPageProps) {
  const { user, loading: authLoading } = useAuth()
  const [scan, setScan] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadCampaignAnalysis = async () => {
      if (!user) {
        if (!authLoading) {
          setError('Not authenticated')
          setLoading(false)
        }
        return
      }

      try {
        const docRef = doc(db, 'users', user.uid, 'scans', params.campaignId)
        const snapshot = await getDoc(docRef)
        if (snapshot.exists()) {
          const savedData = { id: snapshot.id, ...snapshot.data() }
          if (!savedData.analysis && !savedData.result) {
            const response = await detectionAPI.analyzeGoPhishCampaign(params.campaignId)
            console.debug('GET /api/gophish/campaigns/{campaign_id}/analysis response:', response)
            const analysis = response.analysis || response.result
            const template = response.template || {}
            const campaignName = response.campaign_name || response.campaignName || ''
            const scanDoc = {
              id: params.campaignId,
              type: 'email',
              source: 'gophish',
              campaign_id: params.campaignId,
              campaign_name: campaignName,
              subject: template.subject,
              sender_email: template.sender_email,
              createdAt: new Date().toISOString(),
              template,
              analysis,
              result: analysis,
            }
            setScan(scanDoc)
            try {
              await setDoc(doc(db, 'users', user.uid, 'scans', params.campaignId), scanDoc)
            } catch (saveError: any) {
              console.warn('Unable to save campaign analysis to Firestore:', saveError?.message || saveError)
            }
          } else {
            setScan(savedData)
            if (!savedData.analysis && savedData.result) {
              setScan({ ...savedData, analysis: savedData.result })
            }
          }
        } else {
          const response = await detectionAPI.analyzeGoPhishCampaign(params.campaignId)
          console.debug('GET /api/gophish/campaigns/{campaign_id}/analysis response:', response)
          const analysis = response.analysis || response.result
          const template = response.template || {}
          const campaignName = response.campaign_name || response.campaignName || ''
          const scanDoc = {
            id: params.campaignId,
            type: 'email',
            source: 'gophish',
            campaign_id: params.campaignId,
            campaign_name: campaignName,
            subject: template.subject,
            sender_email: template.sender_email,
            createdAt: new Date().toISOString(),
            template,
            analysis,
            result: analysis,
          }
          setScan(scanDoc)
          try {
            await setDoc(doc(db, 'users', user.uid, 'scans', params.campaignId), scanDoc)
          } catch (saveError: any) {
            console.warn('Unable to save campaign analysis to Firestore:', saveError?.message || saveError)
          }
        }
      } catch (err: any) {
        setError(err?.message || 'Unable to load campaign analysis')
      } finally {
        setLoading(false)
      }
    }

    loadCampaignAnalysis()
  }, [user, authLoading, params.campaignId])

  return (
    <DashboardLayout>
      <div className="p-6 max-w-4xl space-y-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold">Campaign Details</h1>
            <p className="text-gray-600">Review the GoPhish campaign email analysis and risk summary.</p>
          </div>
          <Link href="/dashboard">
            <Badge label="Back to Dashboard" variant="default" />
          </Link>
        </div>

        {error && <Alert variant="error">{error}</Alert>}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-12 h-12 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
          </div>
        ) : scan ? (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>{scan.campaign_name || scan.subject || 'Campaign Analysis'}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-sm text-gray-500">Risk Level</p>
                    <p className="font-semibold">{scan.analysis?.risk_level || scan.result?.risk_level || ''}</p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-sm text-gray-500">AI Verdict</p>
                    <p className="font-semibold">{scan.analysis?.label || scan.result?.label || ''}</p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-sm text-gray-500">Risk Score</p>
                    <p className="font-semibold">
                      {typeof scan.analysis?.phishing_probability === 'number'
                        ? `${Math.round(scan.analysis.phishing_probability * 100)}%`
                        : typeof scan.result?.risk_score === 'number'
                        ? `${Math.round(scan.result.risk_score)}%`
                        : ''}
                    </p>
                  </div>
                </div>

                <div className="mt-6 space-y-4">
                  {scan.subject || scan.template?.subject ? (
                    <div>
                      <h3 className="text-lg font-semibold">Subject</h3>
                      <p className="text-sm text-gray-700">{scan.subject || scan.template?.subject}</p>
                    </div>
                  ) : null}
                  {scan.sender_email || scan.template?.sender_email ? (
                    <div>
                      <h3 className="text-lg font-semibold">Sender</h3>
                      <p className="text-sm text-gray-700">{scan.sender_email || scan.template?.sender_email}</p>
                    </div>
                  ) : null}
                  <div>
                    <h3 className="text-lg font-semibold">URLs</h3>
                    <div className="space-y-1">
                      {scan.template?.url_list?.length ? (
                        scan.template.url_list.map((url: string, index: number) => (
                          <a key={index} href={url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline block truncate">
                            {url}
                          </a>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500">No URLs detected.</p>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Analysis Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold">Red Flags</h3>
                    {scan.analysis?.reasons?.length ? (
                      <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                        {scan.analysis.reasons.map((reason: string, index: number) => (
                          <li key={index}>{reason}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-gray-500">No red flags detected.</p>
                    )}
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold">Recommendations</h3>
                    {scan.analysis?.recommendations?.length ? (
                      <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                        {scan.analysis.recommendations.map((recommendation: string, index: number) => (
                          <li key={index}>{recommendation}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-gray-500">No recommendations available.</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </div>
    </DashboardLayout>
  )
}
