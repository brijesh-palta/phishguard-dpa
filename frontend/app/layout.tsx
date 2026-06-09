import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PhishGuard - Email & URL Security Scanner',
  description: 'AI-powered phishing detection and email security analysis',
  icons: {
    icon: '🛡️',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-white text-black font-sans antialiased">
        {children}
      </body>
    </html>
  )
}
