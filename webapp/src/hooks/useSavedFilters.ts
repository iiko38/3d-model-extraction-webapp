import { useState, useEffect, useCallback } from 'react'

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

const STORAGE_KEY = 'saved-filters'

export function useSavedFilters() {
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([])

  // Load saved filters from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        setSavedFilters(Array.isArray(parsed) ? parsed : [])
      }
    } catch (error) {
      console.error('Failed to load saved filters:', error)
    }
  }, [])

  // Save filters to localStorage
  const saveToStorage = useCallback((filters: SavedFilter[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filters))
    } catch (error) {
      console.error('Failed to save filters:', error)
    }
  }, [])

  // Save current filter set
  const saveFilter = useCallback((name: string, filters: Filters) => {
    const newFilter: SavedFilter = {
      id: Date.now().toString(),
      name,
      filters,
      createdAt: Date.now()
    }

    const updated = [...savedFilters, newFilter]
    setSavedFilters(updated)
    saveToStorage(updated)
    
    return newFilter
  }, [savedFilters, saveToStorage])

  // Delete saved filter
  const deleteFilter = useCallback((id: string) => {
    const updated = savedFilters.filter(filter => filter.id !== id)
    setSavedFilters(updated)
    saveToStorage(updated)
  }, [savedFilters, saveToStorage])

  // Check if current filters match a saved filter
  const isCurrentFilterSaved = useCallback((currentFilters: Filters) => {
    return savedFilters.some(saved => {
      return Object.keys(currentFilters).every(key => {
        const k = key as keyof Filters
        return saved.filters[k] === currentFilters[k]
      })
    })
  }, [savedFilters])

  // Get saved filter by ID
  const getFilterById = useCallback((id: string) => {
    return savedFilters.find(filter => filter.id === id)
  }, [savedFilters])

  return {
    savedFilters,
    saveFilter,
    deleteFilter,
    isCurrentFilterSaved,
    getFilterById
  }
}
