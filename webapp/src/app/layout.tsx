import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '3D Model Library',
  description: 'Advanced 3D model management system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-background">
          <nav className="bg-card shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex">
                  <div className="flex-shrink-0 flex items-center">
                    <a href="/" className="text-xl font-bold text-foreground">
                      3D Model Library
                    </a>
                  </div>
                  <div className="hidden md:block">
                    <div className="ml-10 flex items-baseline space-x-4">
                      <a href="/" className="text-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium">Files</a>
                      <a href="/cards" className="text-muted-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium">Cards</a>
                      <a href="/stats" className="text-muted-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium">Statistics</a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </nav>
          <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
