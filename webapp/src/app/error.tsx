'use client'

import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Global error caught:', error)
  }, [error])

  return (
    <div className="p-6">
      <Card>
        <CardHeader>
          <CardTitle>Something went wrong!</CardTitle>
          <CardDescription>An unexpected error occurred</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="text-red-600 bg-red-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Error Details</h3>
              <p className="text-sm">{error.message}</p>
              {error.digest && (
                <p className="text-xs mt-2 text-gray-500">Error ID: {error.digest}</p>
              )}
            </div>
            
            <div className="flex space-x-2">
              <Button onClick={reset} variant="default">
                Try again
              </Button>
              <Button onClick={() => window.location.href = '/'} variant="outline">
                Go home
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
