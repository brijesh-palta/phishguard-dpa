'use client'

import Link from 'next/link'
import { useAuth } from '@/lib/hooks'
import { Button } from '@/components/ui/Button'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function Home() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (user && !loading) {
      router.push('/dashboard')
    }
  }, [user, loading, router])

  if (loading) {
    return null
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="text-2xl font-bold">PhishGuard</div>
        <div className="space-x-4">
          <Link href="/login">
            <Button variant="ghost" className="text-white border-white">
              Login
            </Button>
          </Link>
          <Link href="/signup">
            <Button>Sign Up</Button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="space-y-6 text-center">
          <h1 className="text-5xl md:text-6xl font-bold leading-tight">
            Detect Phishing
            <br />
            <span className="text-gray-400">Before It Happens</span>
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            AI-powered email and URL analysis. Scan for threats in seconds.
            Protect your inbox from phishing attacks with advanced machine
            learning.
          </p>

          <div className="flex gap-4 justify-center pt-8">
            <Link href="/signup">
              <Button size="lg">Get Started Free</Button>
            </Link>
            <a href="#features">
              <Button size="lg" variant="ghost" className="border-white">
                Learn More
              </Button>
            </a>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="bg-gray-900 border-y border-gray-800 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-12 text-center">
            Powerful Security Features
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: 'Email',
                title: 'Email Analysis',
                desc: 'Scan email content, headers, and attachments for phishing indicators',
              },
              {
                icon: 'URL',
                title: 'URL Detection',
                desc: 'Identify malicious links and suspicious URL patterns instantly',
              },
              {
                icon: 'AI',
                title: 'AI-Powered',
                desc: 'Machine learning models trained on thousands of phishing samples',
              },
              {
                icon: 'Realtime',
                title: 'Real-time Analysis',
                desc: 'Get instant results with confidence scores and risk assessment',
              },
              {
                icon: 'History',
                title: 'History Tracking',
                desc: 'Track all scans and maintain a comprehensive security history',
              },
              {
                icon: 'Simulation',
                title: 'Phishing Simulation',
                desc: 'Launch interactive training scenarios to level up employee awareness',
              },
              {
                icon: 'Secure',
                title: 'Private & Secure',
                desc: 'Your data is encrypted and never shared with third parties',
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="bg-black border border-gray-800 rounded-lg p-6 hover:border-gray-600 transition-colors"
              >
                <div className="text-sm font-semibold uppercase tracking-wide mb-4 text-gray-300">{feature.icon}</div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold mb-12 text-center">How It Works</h2>
        <div className="space-y-8">
          {[
            {
              num: '1',
              title: 'Create Account',
              desc: 'Sign up in seconds with your email',
            },
            {
              num: '2',
              title: 'Submit Content',
              desc: 'Paste email text or enter a URL to analyze',
            },
            {
              num: '3',
              title: 'Get Analysis',
              desc: 'Receive instant threat assessment and risk score',
            },
            {
              num: '4',
              title: 'View History',
              desc: 'Track all scans and maintain security records',
            },
          ].map((step, i) => (
            <div key={i} className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-black text-white rounded-lg flex items-center justify-center font-bold flex-shrink-0">
                {step.num}
              </div>
              <div>
                <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                <p className="text-gray-600">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-black border-t border-gray-800 py-16">
        <div className="max-w-2xl mx-auto text-center px-6">
          <h2 className="text-3xl font-bold mb-4">Ready to Protect Your Inbox?</h2>
          <p className="text-gray-400 mb-8">
            Join thousands of users protecting themselves from phishing attacks
          </p>
          <Link href="/signup">
            <Button size="lg">Start Free Trial</Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8 text-center text-gray-500 text-sm">
        <p>&copy; 2024 PhishGuard. All rights reserved.</p>
      </footer>
    </div>
  )
}




