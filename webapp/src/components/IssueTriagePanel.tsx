'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertTriangle, Clock, User, FileText } from 'lucide-react'
import { useToast } from '@/components/ui/toast'

interface Issue {
  id: number
  sha256: string
  description: string
  status: 'open' | 'resolved' | 'in_progress'
  created_at: string
  user_email: string
}

interface IssueTriagePanelProps {
  isAdmin: boolean
}

export default function IssueTriagePanel({ isAdmin }: IssueTriagePanelProps) {
  const [issues, setIssues] = useState<Issue[]>([])
  const [loading, setLoading] = useState(false)
  const { addToast } = useToast()

  useEffect(() => {
    if (isAdmin) {
      fetchIssues()
    }
  }, [isAdmin])

  const fetchIssues = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/issues?limit=10')
      if (!response.ok) {
        throw new Error('Failed to fetch issues')
      }
      
      const data = await response.json()
      setIssues(data.issues || [])
    } catch (error) {
      console.error('Failed to fetch issues:', error)
      addToast('Failed to load issue reports', 'error')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'resolved':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 1) {
      return 'Just now'
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`
    } else {
      const diffInDays = Math.floor(diffInHours / 24)
      return `${diffInDays}d ago`
    }
  }

  if (!isAdmin) {
    return null
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          Issue Triage
          <Badge variant="secondary" className="ml-auto">
            {issues.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
            <div className="text-sm text-muted-foreground mt-2">Loading issues...</div>
          </div>
        ) : issues.length === 0 ? (
          <div className="text-center py-4 text-muted-foreground">
            <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No issues reported</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {issues.map((issue) => (
              <div
                key={issue.id}
                className="p-3 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {issue.description}
                    </p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                      <User className="h-3 w-3" />
                      <span className="truncate">{issue.user_email}</span>
                      <Clock className="h-3 w-3 ml-2" />
                      <span>{formatDate(issue.created_at)}</span>
                    </div>
                    <div className="mt-1">
                      <code className="text-xs bg-muted px-1 py-0.5 rounded">
                        {issue.sha256.slice(0, 8)}...
                      </code>
                    </div>
                  </div>
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${getStatusColor(issue.status)}`}
                  >
                    {issue.status.replace('_', ' ')}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {issues.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={fetchIssues}
            disabled={loading}
            className="w-full"
          >
            Refresh Issues
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
