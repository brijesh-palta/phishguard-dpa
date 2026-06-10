'use client'

import { useEffect, useState } from 'react'
import { DashboardLayout } from '@/components/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Alert } from '@/components/ui/Alert'
import { detectionAPI } from '@/lib/api'
import Link from 'next/link'
import { Badge } from '@/components/ui/Badge'
import { useAuth } from '@/lib/hooks'
import { db } from '@/lib/firebase'
import { collection, doc, getDocs, setDoc } from 'firebase/firestore'

export default function Dashboard() {
  const { user } = useAuth()
  const [metrics, setMetrics] = useState<any>(null)
  const [recentScans, setRecentScans] = useState<any[]>([])
  const [gophishStatus, setGophishStatus] = useState<any>(null)
  const [gophishCampaigns, setGophishCampaigns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [gophishLoading, setGophishLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [gophishError, setGophishError] = useState<string | null>(null)

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const [metricsData, detectionData] = await Promise.all([
          detectionAPI.getMetrics(),
          detectionAPI.getDetectionHistory(5),
        ])
        setMetrics(metricsData)
        setRecentScans(detectionData.items || [])
      } catch (err) {
        setError('Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }

    const loadGoPhish = async () => {
      try {
        const statusResponse = await detectionAPI.getGoPhishStatus()
        setGophishStatus(statusResponse)
        if (statusResponse?.configured && statusResponse?.reachable) {
          const campaigns = await detectionAPI.getGoPhishCampaigns()
          if (user && campaigns.length) {
            const now = new Date().toISOString()
            const savedScans: Record<string, any> = {}
            try {
              const scanQuery = await getDocs(collection(db, 'users', user.uid, 'scans'))
              scanQuery.docs.forEach((saved) => {
                const savedData = saved.data()
                if (savedData?.campaign_id) {
                  savedScans[String(savedData.campaign_id)] = { id: saved.id, ...savedData }
                }
              })
            } catch (err: any) {
              console.warn('Failed to load saved GoPhish analysis from Firebase:', err?.message || err)
            }

            const campaignsWithAnalysis = await Promise.all(
              campaigns.map(async (campaign: any) => {
                const campaignId = String(campaign.id ?? campaign.uid ?? campaign.name ?? `campaign-${Math.random().toString(36).slice(2)}`)
                const savedScan = savedScans[campaignId]
                let analysis = savedScan?.result
                let template = savedScan?.template
                let campaignName = savedScan?.campaign_name || campaign.name

                if (!analysis) {
                  try {
                    const response = await detectionAPI.analyzeGoPhishCampaign(campaignId)
                    analysis = response.analysis
                    template = response.template
                    campaignName = response.campaign_name || campaign.name
                    await setDoc(doc(db, 'users', user.uid, 'scans', campaignId), {
                      id: campaignId,
                      type: 'email',
                      source: 'gophish',
                      campaign_id: campaignId,
                      campaign_name: campaignName,
                      subject: template?.subject || campaign.name,
                      sender_email: template?.sender_email || '',
                      createdAt: now,
                      template: {
                        subject: template?.subject,
                        sender_email: template?.sender_email,
                        reply_to_email: template?.reply_to_email,
                        text_body: template?.text_body,
                        html_body: template?.html_body,
                        url_list: template?.url_list || [],
                      },
                      result: analysis,
                    })
                  } catch (err: any) {
                    console.warn(`Failed to fetch campaign analysis for ${campaignId}:`, err?.message || err)
                  }
                }

                try {
                  await setDoc(doc(db, 'users', user.uid, 'gophish_campaigns', campaignId), {
                    ...campaign,
                    savedAt: now,
                    analysis,
                    template,
                    campaign_name: campaignName,
                  })
                } catch (err: any) {
                  console.warn(`Failed to save GoPhish campaign metadata for ${campaignId}:`, err?.message || err)
                }

                try {
                  const results = await detectionAPI.getGoPhishCampaignResults(campaignId)
                  const events = Array.isArray(results)
                    ? results
                    : Array.isArray(results?.items)
                    ? results.items
                    : results?.results || []
                  await Promise.all(
                    events.map(async (event: any, index: number) => {
                      const eventId = String(event?.id ?? event?.result_id ?? `${campaignId}-${index}`)
                      await setDoc(doc(db, 'users', user.uid, 'gophish_events', eventId), {
                        campaign_id: campaignId,
                        campaign_name: campaign.name,
                        ...event,
                        savedAt: now,
                      })
                    })
                  )
                } catch (err: any) {
                  console.warn(`GoPhish event sync failed for ${campaignId}:`, err?.message || err)
                }

                return {
                  ...campaign,
                  id: campaignId,
                  analysis,
                  template,
                  campaign_name: campaignName,
                }
              })
            )
            setGophishCampaigns(campaignsWithAnalysis)
          } else {
            setGophishCampaigns(campaigns)
          }
        }
      } catch (err: any) {
        setGophishError(err?.message || 'Unable to fetch GoPhish data')
      } finally {
        setGophishLoading(false)
      }
    }

    loadMetrics()
    loadGoPhish()
  }, [user])

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-gray-600">Welcome back! Here is your security overview.</p>
        </div>

        {error && <Alert variant="error">{error}</Alert>}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-12 h-12 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            {metrics && (
              <div className="grid md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-black">
                        {metrics.total_users || 0}
                      </div>
                      <p className="text-sm text-gray-600 mt-2">Total Users</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-red-600">
                        {metrics.detection_total || 0}
                      </div>
                      <p className="text-sm text-gray-600 mt-2">Detections</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-yellow-600">
                        {metrics.phishing_detected || 0}
                      </div>
                      <p className="text-sm text-gray-600 mt-2">Phishing Found</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600">
                        {metrics.legitimate_detected || 0}
                      </div>
                      <p className="text-sm text-gray-600 mt-2">Safe Emails</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Quick Actions */}
            <div className="grid md:grid-cols-2 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold mb-1">Scan an Email</h3>
                      <p className="text-sm text-gray-600">
                        Analyze email content for phishing threats
                      </p>
                    </div>
                    <span className="text-3xl">📧</span>
                  </div>
                  <Link href="/scanner/email">
                    <Button className="w-full mt-4">Start Scan</Button>
                  </Link>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold mb-1">Check a URL</h3>
                      <p className="text-sm text-gray-600">
                        Verify if a link is safe or malicious
                      </p>
                    </div>
                    <span className="text-3xl">🔗</span>
                  </div>
                  <Link href="/scanner/url">
                    <Button className="w-full mt-4">Start Scan</Button>
                  </Link>
                </CardContent>
              </Card>
            </div>

            <div className="grid md:grid-cols-1 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold mb-1">Simulation Lab</h3>
                      <p className="text-sm text-gray-600">
                        Generate phishing training scenarios and practice reporting.
                      </p>
                    </div>
                    <span className="text-3xl">🎯</span>
                  </div>
                  <Link href="/dashboard/simulation">
                    <Button className="w-full mt-4">Open Simulation</Button>
                  </Link>
                </CardContent>
              </Card>
            </div>

            {/* GoPhish Summary */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>GoPhish Campaigns</CardTitle>
                  <Link href="/dashboard/simulation">
                    <Button variant="ghost" size="sm">
                      Simulation Lab →
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {gophishLoading ? (
                  <div className="flex justify-center py-8">
                    <div className="w-10 h-10 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
                  </div>
                ) : gophishError ? (
                  <p className="text-red-600">{gophishError}</p>
                ) : gophishStatus?.configured ? (
                  <div className="space-y-4">
                    <div className="grid gap-4 sm:grid-cols-3">
                      <div className="rounded-xl bg-slate-50 p-4">
                        <p className="text-sm text-gray-500">Status</p>
                        <p className="font-semibold">{gophishStatus.reachable ? 'Connected' : 'Configured'}</p>
                      </div>
                      <div className="rounded-xl bg-slate-50 p-4">
                        <p className="text-sm text-gray-500">Campaigns</p>
                        <p className="font-semibold">{gophishCampaigns.length}</p>
                      </div>
                      <div className="rounded-xl bg-slate-50 p-4">
                        <p className="text-sm text-gray-500">Base URL</p>
                        <p className="font-semibold truncate">{gophishStatus.base_url}</p>
                      </div>
                    </div>
                    {gophishCampaigns.length === 0 ? (
                      <p className="text-gray-600">No GoPhish campaigns found yet.</p>
                    ) : (
                      <div className="space-y-3">
                        {gophishCampaigns.slice(0, 3).map((campaign: any) => {
                          const campaignId = String(campaign.id ?? campaign.uid ?? campaign.name)
                          return (
                            <Link key={campaignId} href={`/dashboard/campaigns/${encodeURIComponent(campaignId)}`}> 
                              <div className="rounded-xl border border-gray-200 p-4 bg-white hover:shadow-sm transition-shadow cursor-pointer">
                                <div className="flex items-center justify-between gap-4">
                                  <div>
                                    <p className="text-sm text-gray-500">{campaign.name}</p>
                                    <p className="font-semibold">{campaign.status || campaign.state || 'Draft'}</p>
                                    {campaign.analysis?.label && (
                                      <p className="text-xs text-gray-500 mt-1">
                                        Analysis: {campaign.analysis.label.toUpperCase()} • Risk {campaign.analysis.risk_level || 'unknown'}
                                      </p>
                                    )}
                                  </div>
                                  <Badge label={campaign.status?.toUpperCase() || 'UNKNOWN'} variant={campaign.status === 'live' ? 'safe' : 'phishing'} />
                                </div>
                              </div>
                            </Link>
                          )
                        })}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-gray-600">
                    <p>GoPhish is not configured yet. Set GOPHISH_BASE_URL and GOPHISH_API_KEY in the backend environment.</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* GoPhish Analysis */}
            {gophishCampaigns.some((campaign) => campaign.analysis) && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>GoPhish Campaign Analysis</CardTitle>
                    <Link href="/dashboard/history">
                      <Button variant="ghost" size="sm">
                        View All Scans →
                      </Button>
                    </Link>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {gophishCampaigns.filter((campaign) => campaign.analysis).slice(0, 3).map((campaign: any) => (
                      <div key={campaign.id} className="rounded-xl border border-gray-200 p-4 bg-white">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <div>
                            <p className="text-sm text-gray-500">{campaign.campaign_name || campaign.name}</p>
                            <p className="font-semibold">{campaign.template?.subject || 'No subject available'}</p>
                          </div>
                          <div className="space-x-2">
                            <Link href={`/dashboard/campaigns/${encodeURIComponent(campaign.id)}`}>
                              <Button variant="outline" size="sm">
                                View Analysis
                              </Button>
                            </Link>
                          </div>
                        </div>
                        <div className="mt-4 grid gap-4 sm:grid-cols-4">
                          <div>
                            <p className="text-xs text-gray-500">Sender</p>
                            <p className="font-semibold truncate">{campaign.template?.sender_email || ''}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Risk Score</p>
                            <p className="font-semibold">
                              {typeof campaign.analysis?.phishing_probability === 'number'
                                ? `${Math.round(campaign.analysis.phishing_probability * 100)}%`
                                : ''}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Threat Level</p>
                            <p className="font-semibold">{campaign.analysis?.risk_level || ''}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">AI Verdict</p>
                            <p className="font-semibold">{campaign.analysis?.label?.toUpperCase() || ''}</p>
                          </div>
                        </div>
                        <div className="mt-4 grid gap-4 sm:grid-cols-2">
                          <div>
                            <p className="text-xs text-gray-500">Confidence</p>
                            <p className="font-semibold">{typeof campaign.analysis?.confidence === 'number' ? `${Math.round(campaign.analysis.confidence * 100)}%` : ''}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Red Flags</p>
                            <p className="font-semibold truncate">{campaign.analysis?.reasons?.slice(0, 2).join(', ') || ''}</p>
                          </div>
                        </div>
                        <div className="mt-4">
                          <p className="text-xs text-gray-500">Recommendations</p>
                          <ul className="list-disc list-inside text-sm text-gray-700 mt-2">
                            {(campaign.analysis?.recommendations || []).slice(0, 3).map((rec: string, index: number) => (
                              <li key={index}>{rec}</li>
                            ))}
                            {!campaign.analysis?.recommendations?.length && <li>No recommendations available.</li>}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Recent Scans */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Recent Scans</CardTitle>
                  <Link href="/history">
                    <Button variant="ghost" size="sm">
                      View All →
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {recentScans.length === 0 ? (
                  <p className="text-gray-600 text-center py-8">
                    No scans yet. Start by scanning an email or URL.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {recentScans.map((scan: any) => (
                      <div
                        key={scan.id}
                        className="flex items-start justify-between pb-4 border-b border-gray-200 last:border-0"
                      >
                        <div className="flex-1">
                          <h4 className="font-semibold truncate max-w-md">
                            {scan.subject || 'URL Scan'}
                          </h4>
                          <p className="text-sm text-gray-500 mt-1">
                            {new Date(scan.timestamp).toLocaleDateString()} at{' '}
                            {new Date(scan.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                        <Badge
                          label={scan.prediction?.label?.toUpperCase() || 'UNKNOWN'}
                          variant={
                            scan.prediction?.label === 'phishing'
                              ? 'phishing'
                              : 'safe'
                          }
                        />
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
