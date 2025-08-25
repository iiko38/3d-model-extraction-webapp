import { useCallback, useRef } from 'react'
import { supabase } from '@/lib/supabase'

interface File {
  sha256: string
  name: string
  file_type: string
  size_bytes: number
  brand: string
  furniture_type: string
  status: string
  thumbnail_url: string
  source_url: string
  product_url?: string
  created_at: string
  updated_at?: string
  description?: string
  tags?: string[]
  product_slug?: string
}

interface PrefetchCache {
  [sha256: string]: {
    data: File[]
    timestamp: number
  }
}

const PREFETCH_CACHE_DURATION = 5 * 60 * 1000 // 5 minutes
const prefetchCache: PrefetchCache = {}

export function usePrefetch() {
  const prefetchTimeoutRef = useRef<NodeJS.Timeout>()

  const prefetchSiblingFiles = useCallback(async (file: File) => {
    if (!file.product_slug || !file.brand) return

    // Check cache first
    const cacheKey = `${file.product_slug}-${file.brand}`
    const cached = prefetchCache[cacheKey]
    if (cached && Date.now() - cached.timestamp < PREFETCH_CACHE_DURATION) {
      return cached.data
    }

    try {
      const { data, error } = await supabase
        .from('files')
        .select('*')
        .eq('product_slug', file.product_slug)
        .eq('brand', file.brand)
        .neq('sha256', file.sha256)
        .order('file_type', { ascending: true })

      if (error) throw error

      // Cache the result
      prefetchCache[cacheKey] = {
        data: data || [],
        timestamp: Date.now()
      }

      return data || []
    } catch (error) {
      console.error('Prefetch failed:', error)
      return []
    }
  }, [])

  const prefetchOnFocus = useCallback((file: File) => {
    // Clear any existing timeout
    if (prefetchTimeoutRef.current) {
      clearTimeout(prefetchTimeoutRef.current)
    }

    // Prefetch after a short delay to avoid excessive requests
    prefetchTimeoutRef.current = setTimeout(() => {
      prefetchSiblingFiles(file)
    }, 100)
  }, [prefetchSiblingFiles])

  const prefetchOnHover = useCallback((file: File) => {
    // Clear any existing timeout
    if (prefetchTimeoutRef.current) {
      clearTimeout(prefetchTimeoutRef.current)
    }

    // Prefetch immediately on hover
    prefetchSiblingFiles(file)
  }, [prefetchSiblingFiles])

  const clearPrefetchTimeout = useCallback(() => {
    if (prefetchTimeoutRef.current) {
      clearTimeout(prefetchTimeoutRef.current)
    }
  }, [])

  return {
    prefetchOnFocus,
    prefetchOnHover,
    clearPrefetchTimeout,
    prefetchSiblingFiles
  }
}
