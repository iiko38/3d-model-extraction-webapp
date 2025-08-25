import { useState, useEffect, useRef, useCallback } from 'react'
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
  _score?: number
}

interface SearchResult {
  files: File[]
  loading: boolean
  error: string | null
  pagination: {
    page: number
    totalPages: number
    totalCount: number
    hasNext: boolean
    hasPrev: boolean
  }
}

interface SearchParams {
  q: string
  type: string
  brand: string
  cat: string
  status: string
  min: string
  max: string
  sort: string
}

export function useHybridSearch() {
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({
    page: 1,
    totalPages: 1,
    totalCount: 0,
    hasNext: false,
    hasPrev: false
  })
  
  const searchTimeoutRef = useRef<NodeJS.Timeout>()
  const currentSearchRef = useRef<string>('')
  const abortControllerRef = useRef<AbortController | null>(null)

  // Simple search for queries < 3 characters
  const simpleSearch = useCallback(async (params: SearchParams, page: number = 1) => {
    // Abort any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    // Create new abort controller for this request
    abortControllerRef.current = new AbortController()
    
    setLoading(true)
    setError(null)
    
    try {
      // Try to use the new search_files RPC if available, fallback to simple query
      try {
        const { data, error } = await supabase.rpc('search_files', {
          query: params.q || null,
          file_type_filter: params.type !== 'all' ? params.type : null,
          brand_filter: params.brand !== 'all' ? params.brand : null,
          furniture_type_filter: params.cat !== 'all' ? params.cat : null,
          status_filter: params.status !== 'all' ? params.status : null,
          min_size: params.min ? parseInt(params.min) * 1024 * 1024 : null, // Convert MB to bytes
          max_size: params.max ? parseInt(params.max) * 1024 * 1024 : null, // Convert MB to bytes
          sort_by: params.sort,
          sort_order: params.sort === 'name' ? 'asc' : 'desc',
          page_num: page,
          page_size: 20
        })
        
        if (error) throw error
        
        if (!data || data.length === 0) {
          setFiles([])
          setPagination({
            page,
            totalPages: 0,
            totalCount: 0,
            hasNext: false,
            hasPrev: false
          })
          return
        }
        
        // Extract total count from the first row
        const totalCount = data[0]?.total_count || 0
        const totalPages = Math.ceil(totalCount / 20)
        
        // Remove total_count from results
        const results = data.map((row: any) => {
          const { total_count, ...file } = row
          return file
        })
        
        setFiles(results)
        setPagination({
          page,
          totalPages,
          totalCount,
          hasNext: page < totalPages,
          hasPrev: page > 1
        })
        return
        
      } catch (rpcError) {
        // Fallback to simple query if RPC is not available
        console.warn('RPC not available, falling back to simple query:', rpcError)
      }
      
      // Fallback: Simple query approach
      let query = supabase.from('files').select('*')
      const limit = 20
      const offset = (page - 1) * limit

      // Apply search filter
      if (params.q) {
        query = query.or(`name.ilike.%${params.q}%,brand.ilike.%${params.q}%,furniture_type.ilike.%${params.q}%`)
      }

      // Apply other filters
      if (params.type !== 'all') query = query.eq('file_type', params.type)
      if (params.brand !== 'all') query = query.eq('brand', params.brand)
      if (params.cat !== 'all') query = query.eq('furniture_type', params.cat)
      if (params.status !== 'all') query = query.eq('status', params.status)
      if (params.min) query = query.gte('size_bytes', parseInt(params.min))
      if (params.max) query = query.lte('size_bytes', parseInt(params.max))

      // Apply sorting
      const sortOrder = params.sort === 'name' ? 'asc' : 'desc'
      query = query.order(params.sort, { ascending: sortOrder === 'asc' })

      // Apply pagination
      query = query.range(offset, offset + limit - 1)

      const result = await query
      if (result.error) throw result.error

      // Get total count
      const countQuery = supabase.from('files').select('*', { count: 'exact', head: true })
      if (params.q) {
        countQuery.or(`name.ilike.%${params.q}%,brand.ilike.%${params.q}%,furniture_type.ilike.%${params.q}%`)
      }
      const countResult = await countQuery
      const totalCount = countResult.count || 0

      setFiles(result.data || [])
      setPagination({
        page,
        totalPages: Math.ceil(totalCount / limit),
        totalCount,
        hasNext: page < Math.ceil(totalCount / limit),
        hasPrev: page > 1
      })
    } catch (err: any) {
      // Don't set error if request was aborted
      if (err.name !== 'AbortError') {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  // Ranked search for queries >= 3 characters
  const rankedSearch = useCallback(async (params: SearchParams, page: number = 1) => {
    // Abort any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    // Create new abort controller for this request
    abortControllerRef.current = new AbortController()
    
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(params.q)}&page=${page}&limit=20`, {
        signal: abortControllerRef.current?.signal
      })
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Search failed')
      }

      setFiles(data.results || [])
      setPagination(data.pagination || {
        page: 1,
        totalPages: 1,
        totalCount: 0,
        hasNext: false,
        hasPrev: false
      })
    } catch (err: any) {
      // Don't set error if request was aborted
      if (err.name !== 'AbortError') {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  // Main search function
  const search = useCallback(async (params: SearchParams, page: number = 1) => {
    // Cancel previous search if it's still running
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    // Debounce search
    searchTimeoutRef.current = setTimeout(async () => {
      currentSearchRef.current = params.q
      
      if (params.q.length < 3) {
        await simpleSearch(params, page)
      } else {
        await rankedSearch(params, page)
      }
    }, 300) // 300ms debounce
  }, [simpleSearch, rankedSearch])

  // Load more results
  const loadMore = useCallback(async (params: SearchParams) => {
    if (pagination.hasNext && !loading) {
      const nextPage = pagination.page + 1
      if (params.q.length < 3) {
        await simpleSearch(params, nextPage)
      } else {
        await rankedSearch(params, nextPage)
      }
    }
  }, [pagination, loading, simpleSearch, rankedSearch])

  // Clear search
  const clearSearch = useCallback(() => {
    setFiles([])
    setError(null)
    setPagination({
      page: 1,
      totalPages: 1,
      totalCount: 0,
      hasNext: false,
      hasPrev: false
    })
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  return {
    files,
    loading,
    error,
    pagination,
    search,
    loadMore,
    clearSearch
  }
}
