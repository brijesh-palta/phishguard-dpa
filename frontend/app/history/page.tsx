'use client'

import { useEffect, useState } from 'react'
import { DashboardLayout } from '@/components/DashboardLayout'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { db } from '@/lib/firebase'
import { collection, query, orderBy, getDocs } from 'firebase/firestore'
import { useAuth } from '@/lib/hooks'

export default function HistoryPage() {
  const { user, loading: authLoading } = useAuth()
  const [scans, setScans] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadScans = async () => {
      if (!user) {
        if (!authLoading) {
          setError('Not authenticated')
          setLoading(false)
        }
        return
      }

      try {
        const q = query(
          collection(db, 'users', user.uid, 'scans'),
          orderBy('createdAt', 'desc')
        )
        const querySnapshot = await getDocs(q)
        const scanData = querySnapshot.docs.map((doc) => ({
          id: doc.id,
          ...doc.data(),
        }))
        setScans(scanData)
      } catch (err: any) {
        setError(err?.message || 'Failed to load scan history')
      } finally {
        setLoading(false)
      }
    }

    loadScans()
  }, [user, authLoading])

  return (
    <DashboardLayout>
      <div className="p-6 max-w-4xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Scan History</h1>
          <p className="text-gray-600">
            View all your previous email and URL scans
          </p>
        </div>

        {error && <Alert variant="error" className="mb-6">{error}</Alert>}

        <Card>
          <CardContent className="pt-6">
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="w-12 h-12 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
              </div>
            ) : scans.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">📭</div>
                <p>No scans yet. Start by scanning an email or URL.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Type
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Content
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Result
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Confidence
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">
                        Date
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {scans.map((scan) => (
                      <tr
                        key={scan.id}
                        className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                      >
                        <td className="py-3 px-4">
                          <span className="inline-block px-2 py-1 bg-gray-200 text-gray-800 rounded text-xs font-semibold">
                            {scan.type === 'email' ? '📧 Email' : '🔗 URL'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm">
                          <div className="max-w-xs truncate">
                            <Link
                              href={
                                scan.source === 'gophish' && scan.campaign_id
                                  ? `/dashboard/campaigns/${encodeURIComponent(scan.campaign_id)}`
                                  : '#'
                              }
                              className="text-blue-600 hover:underline"
                            >
                              {scan.subject || scan.url || 'N/A'}
                            </Link>
                          </div>
                          {scan.sender_email ? (
                            <div className="text-xs text-gray-500 mt-1">
                              {scan.sender_email}
                            </div>
                          ) : null}
                        </td>
                        <td className="py-3 px-4">
                          <Badge
                            label={
                              scan.result?.label?.toUpperCase() || scan.analysis?.label?.toUpperCase() || 'UNKNOWN'
                            }
                            variant={
                              scan.result?.label === 'phishing' || scan.analysis?.label === 'phishing'
                                ? 'phishing'
                                : 'safe'
                            }
                          />
                        </td>
                        <td className="py-3 px-4 text-sm">
                          {scan.result?.confidence
                            ? `${(scan.result.confidence * 100).toFixed(0)}%`
                            : scan.analysis?.phishing_probability
                            ? `${(scan.analysis.phishing_probability * 100).toFixed(0)}%`
                            : 'N/A'}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-500">
                          {scan.createdAt ? new Date(scan.createdAt).toLocaleDateString() : ''} at{' '}
                          {scan.createdAt ? new Date(scan.createdAt).toLocaleTimeString() : ''}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
