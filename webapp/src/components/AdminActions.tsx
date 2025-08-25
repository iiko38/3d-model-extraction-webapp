'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Archive, Image, AlertTriangle } from 'lucide-react'
import { useToast } from '@/components/ui/toast'

interface AdminActionsProps {
  sha256: string
  isAdmin: boolean
  onArchive: () => void
  onThumbnailUpdate: (url: string) => void
}

export default function AdminActions({ 
  sha256, 
  isAdmin, 
  onArchive, 
  onThumbnailUpdate 
}: AdminActionsProps) {
  const [thumbnailUrl, setThumbnailUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [showThumbnailDialog, setShowThumbnailDialog] = useState(false)
  const { addToast } = useToast()

  if (!isAdmin) {
    return null
  }

  const handleArchive = async () => {
    if (!confirm('Are you sure you want to archive this file? This action cannot be undone.')) {
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/files/archive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sha256 })
      })

      if (!response.ok) {
        throw new Error('Failed to archive file')
      }

      addToast('File archived successfully', 'success')
      onArchive()
    } catch (error) {
      console.error('Archive failed:', error)
      addToast('Failed to archive file', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleThumbnailUpdate = async () => {
    if (!thumbnailUrl.trim()) {
      addToast('Please enter a thumbnail URL', 'error')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/files/replace-thumbnail', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sha256, thumbnailUrl: thumbnailUrl.trim() })
      })

      if (!response.ok) {
        throw new Error('Failed to update thumbnail')
      }

      addToast('Thumbnail updated successfully', 'success')
      onThumbnailUpdate(thumbnailUrl.trim())
      setShowThumbnailDialog(false)
      setThumbnailUrl('')
    } catch (error) {
      console.error('Thumbnail update failed:', error)
      addToast('Failed to update thumbnail', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-3 p-4 bg-muted rounded-lg">
      <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
        <AlertTriangle className="h-4 w-4" />
        Admin Actions
      </h3>
      
      <div className="flex gap-2">
        <Dialog open={showThumbnailDialog} onOpenChange={setShowThumbnailDialog}>
          <DialogTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              disabled={loading}
            >
              <Image className="h-4 w-4 mr-2" />
              Replace Thumbnail
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Replace Thumbnail</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label htmlFor="thumbnail-url" className="text-sm font-medium">
                  Thumbnail URL
                </label>
                <Input
                  id="thumbnail-url"
                  type="url"
                  placeholder="https://example.com/image.jpg"
                  value={thumbnailUrl}
                  onChange={(e) => setThumbnailUrl(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleThumbnailUpdate}
                  disabled={loading || !thumbnailUrl.trim()}
                  className="flex-1"
                >
                  {loading ? 'Updating...' : 'Update Thumbnail'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowThumbnailDialog(false)}
                  disabled={loading}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <Button
          variant="destructive"
          size="sm"
          onClick={handleArchive}
          disabled={loading}
          className="flex-1"
        >
          <Archive className="h-4 w-4 mr-2" />
          Archive
        </Button>
      </div>
    </div>
  )
}
