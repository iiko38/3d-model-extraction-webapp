'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Loader2, Play, Eye, RefreshCw } from 'lucide-react'

interface JobResult {
  message: string
  checked: number
  updated: number
  ok: number
  broken: number
  errors: number
  results?: Array<{
    sha256: string
    source_url: string
    link_health: string
    error?: string
  }>
}

export default function AdminPage() {
  const [limit, setLimit] = useState(5)
  const [dryRun, setDryRun] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<JobResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const runJob = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/api/jobs/link-health', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit, dryRun })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Job failed')
      }

      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ok': return 'bg-green-500'
      case 'broken': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground">Manage system jobs and monitor health</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="h-5 w-5" />
              Link Health Checker
            </CardTitle>
            <CardDescription>
              Check the health of file source URLs and update their status in the database
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="limit">Files to Process</Label>
                <Input
                  id="limit"
                  type="number"
                  min="1"
                  max="100"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value) || 5)}
                />
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="dryRun"
                  checked={dryRun}
                  onCheckedChange={(checked) => setDryRun(checked as boolean)}
                />
                <Label htmlFor="dryRun">Dry Run (test without updates)</Label>
              </div>
              <div className="flex items-end">
                <Button 
                  onClick={runJob} 
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Run Job
                    </>
                  )}
                </Button>
              </div>
            </div>

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800 font-medium">Error:</p>
                <p className="text-red-700">{error}</p>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">{result.checked}</div>
                    <div className="text-sm text-blue-700">Checked</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{result.ok}</div>
                    <div className="text-sm text-green-700">Healthy</div>
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">{result.broken}</div>
                    <div className="text-sm text-red-700">Broken</div>
                  </div>
                  <div className="text-center p-4 bg-yellow-50 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-600">{result.errors}</div>
                    <div className="text-sm text-yellow-700">Errors</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">{result.updated}</div>
                    <div className="text-sm text-purple-700">Updated</div>
                  </div>
                </div>

                {result.results && result.results.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-2">Detailed Results:</h3>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {result.results.map((item, index) => (
                        <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                          <div className={`w-3 h-3 rounded-full ${getStatusColor(item.link_health)}`} />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-mono truncate">{item.sha256}</p>
                            <p className="text-xs text-muted-foreground truncate">{item.source_url}</p>
                            {item.error && (
                              <p className="text-xs text-red-600">{item.error}</p>
                            )}
                          </div>
                          <Badge variant={item.link_health === 'ok' ? 'default' : 'destructive'}>
                            {item.link_health}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setLimit(5)
                  setDryRun(true)
                }}
              >
                Test (5 files, dry run)
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setLimit(10)
                  setDryRun(false)
                }}
              >
                Small Run (10 files)
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setLimit(50)
                  setDryRun(false)
                }}
              >
                Medium Run (50 files)
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
