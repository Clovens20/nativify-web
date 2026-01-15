import type { Metadata } from 'next'
import { AuthProvider } from '@/context/AuthContext'
import { Toaster } from 'sonner'
import { VisitTracker } from '@/components/VisitTracker'
import './globals.css'

export const metadata: Metadata = {
  title: 'NativiWeb Studio',
  description: 'Transform your web apps into native mobile applications',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: '#050505',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr" className="dark">
      <head>
        {/* Preconnect to external domains for faster loading */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
      </head>
      <body>
        <AuthProvider>
          <VisitTracker />
          {children}
          <Toaster position="bottom-right" />
        </AuthProvider>
      </body>
    </html>
  )
}
