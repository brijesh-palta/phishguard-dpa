'use client'

import { useEffect, useState } from 'react'
import { DashboardLayout } from '@/components/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Alert } from '@/components/ui/Alert'
import { detectionAPI } from '@/lib/api'
import Link from 'next/link'
import { Badge } from '@/components/ui/Badge'

export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null)
  const [recentScans, setRecentScans] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    loadMetrics()
  }, [])

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
