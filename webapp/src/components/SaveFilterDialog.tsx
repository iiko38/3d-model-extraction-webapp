'use client'

import { useState, forwardRef, useImperativeHandle } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Star } from 'lucide-react'
import { useToast } from '@/components/ui/toast'

interface Filters {
  q: string
  type: string
  brand: string
  cat: string
  status: string
  min: string
  max: string
  sort: string
}

interface SaveFilterDialogProps {
  currentFilters: Filters
  onSaveFilter: (name: string, filters: Filters) => void
  isCurrentFilterSaved: boolean
  children: React.ReactNode
}

export interface SaveFilterDialogRef {
  openDialog: () => void
}

const SaveFilterDialog = forwardRef<SaveFilterDialogRef, SaveFilterDialogProps>(({
  currentFilters,
  onSaveFilter,
  isCurrentFilterSaved,
  children
}, ref) => {
  const [isOpen, setIsOpen] = useState(false)
  const [filterName, setFilterName] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const { addToast } = useToast()

  // Expose open method for external triggers
  useImperativeHandle(ref, () => ({
    openDialog: () => {
      if (!isCurrentFilterSaved) {
        setIsOpen(true)
      }
    }
  }), [isCurrentFilterSaved])

  const handleSave = async () => {
    if (!filterName.trim()) {
      addToast('Please enter a filter name', 'error')
      return
    }

    setIsSaving(true)
    try {
      onSaveFilter(filterName.trim(), currentFilters)
      addToast(`Filter "${filterName.trim()}" saved successfully`, 'success')
      setFilterName('')
      setIsOpen(false)
    } catch (error) {
      addToast('Failed to save filter', 'error')
    } finally {
      setIsSaving(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSave()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Star className="h-5 w-5" />
            Save Filter
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="filter-name">Filter Name</Label>
            <Input
              id="filter-name"
              placeholder="e.g., Large Revit Files, Ikea Chairs..."
              value={filterName}
              onChange={(e) => setFilterName(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
            />
          </div>
          
          <div className="text-sm text-muted-foreground">
            <p className="font-medium mb-2">Current filters:</p>
            <div className="space-y-1">
              {currentFilters.q && <p>Search: "{currentFilters.q}"</p>}
              {currentFilters.type !== 'all' && <p>Type: {currentFilters.type}</p>}
              {currentFilters.brand !== 'all' && <p>Brand: {currentFilters.brand}</p>}
              {currentFilters.cat !== 'all' && <p>Category: {currentFilters.cat}</p>}
              {currentFilters.status !== 'all' && <p>Status: {currentFilters.status}</p>}
              {(currentFilters.min || currentFilters.max) && (
                <p>Size: {currentFilters.min || '0'} - {currentFilters.max || '∞'} MB</p>
              )}
              <p>Sort: {currentFilters.sort}</p>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setIsOpen(false)}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={!filterName.trim() || isSaving}
            >
              {isSaving ? 'Saving...' : 'Save Filter'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
})

SaveFilterDialog.displayName = 'SaveFilterDialog'

export default SaveFilterDialog
