'use client'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { X, Star } from 'lucide-react'
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

interface SavedFilter {
  id: string
  name: string
  filters: Filters
  createdAt: number
}

interface SavedFilterChipsProps {
  savedFilters: SavedFilter[]
  onApplyFilter: (filters: Filters) => void
  onDeleteFilter: (id: string) => void
  currentFilters: Filters
}

export default function SavedFilterChips({
  savedFilters,
  onApplyFilter,
  onDeleteFilter,
  currentFilters
}: SavedFilterChipsProps) {
  const { addToast } = useToast()

  if (savedFilters.length === 0) return null

  const handleApplyFilter = (filter: SavedFilter) => {
    onApplyFilter(filter.filters)
    addToast(`Applied filter: ${filter.name}`, 'success')
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleDeleteFilter = (id: string, name: string) => {
    onDeleteFilter(id)
    addToast(`Deleted filter: ${name}`, 'success')
  }

  // Check if current filters match any saved filter
  const isCurrentFilterSaved = savedFilters.some(saved => {
    return Object.keys(currentFilters).every(key => {
      const k = key as keyof Filters
      return saved.filters[k] === currentFilters[k]
    })
  })

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {savedFilters.map((filter) => {
        const isActive = Object.keys(currentFilters).every(key => {
          const k = key as keyof Filters
          return filter.filters[k] === currentFilters[k]
        })

        return (
          <Badge
            key={filter.id}
            variant={isActive ? "default" : "outline"}
            className={`cursor-pointer hover:bg-primary/90 transition-colors ${
              isActive ? 'ring-2 ring-primary/20' : ''
            }`}
            onClick={() => handleApplyFilter(filter)}
            title={`Apply filter: ${filter.name}`}
          >
            <Star className="h-3 w-3 mr-1" />
            {filter.name}
            <Button
              variant="ghost"
              size="sm"
              className="h-4 w-4 p-0 ml-1 hover:bg-transparent"
              onClick={(e) => {
                e.stopPropagation()
                handleDeleteFilter(filter.id, filter.name)
              }}
              aria-label={`Delete filter: ${filter.name}`}
            >
              <X className="h-3 w-3" />
            </Button>
          </Badge>
        )
      })}
    </div>
  )
}
