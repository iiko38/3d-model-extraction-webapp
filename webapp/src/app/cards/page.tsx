'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { supabase, isSupabaseConfigured } from '@/lib/supabase'
import Image from 'next/image'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Search, MoreHorizontal, Info, Copy, ExternalLink, Star } from 'lucide-react'
import FileDetailsDrawer from '@/components/FileDetailsDrawer'
import CommandPalette from '@/components/CommandPalette'
import FileGridSkeleton from '@/components/FileGridSkeleton'
import VirtualizedGrid from '@/components/VirtualizedGrid'
import PerformanceMonitor from '@/components/PerformanceMonitor'
import SavedFilterChips from '@/components/SavedFilterChips'
import SaveFilterDialog, { SaveFilterDialogRef } from '@/components/SaveFilterDialog'
import { useHybridSearch } from '@/hooks/useHybridSearch'
import { usePrefetch } from '@/hooks/usePrefetch'
import { useSavedFilters } from '@/hooks/useSavedFilters'
import { useToast } from '@/components/ui/toast'

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

export default function FilesPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { addToast } = useToast()
  
  const [imageError, setImageError] = useState<Set<string>>(new Set())
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerFileIndex, setDrawerFileIndex] = useState(-1)
  const [currentDrawerFile, setCurrentDrawerFile] = useState<File | null>(null)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  
  // Hybrid search hook
  const { files, loading, error, pagination, search, loadMore } = useHybridSearch()
  
  // Prefetch hook
  const { prefetchOnFocus, prefetchOnHover, clearPrefetchTimeout } = usePrefetch()
  
  // Saved filters hook
  const { savedFilters, saveFilter, deleteFilter, isCurrentFilterSaved } = useSavedFilters()
  
  // Filter options
  const [fileTypes, setFileTypes] = useState<string[]>([])
  const [brands, setBrands] = useState<string[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [statuses, setStatuses] = useState<string[]>([])
  
  // Performance monitoring (enabled in development or when files > 200)
  const shouldMonitorPerformance = process.env.NODE_ENV === 'development' || files.length > 200
  
  // Refs
  const searchRef = useRef<HTMLInputElement>(null)
  const moreFiltersRef = useRef<HTMLButtonElement>(null)
  const cardRefs = useRef<(HTMLDivElement | null)[]>([])
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const saveFilterDialogRef = useRef<SaveFilterDialogRef>(null)

  // Get filters from URL
  const getFiltersFromURL = (): Filters => ({
    q: searchParams.get('q') || '',
    type: searchParams.get('type') || 'all',
    brand: searchParams.get('brand') || 'all',
    cat: searchParams.get('cat') || 'all',
    status: searchParams.get('status') || 'all',
    min: searchParams.get('min') || '',
    max: searchParams.get('max') || '',
    sort: searchParams.get('sort') || 'created_at'
  })

  // Update URL with filters
  const updateURL = useCallback((filters: Partial<Filters>) => {
    const current = getFiltersFromURL()
    const newFilters = { ...current, ...filters }
    
    const params = new URLSearchParams()
    Object.entries(newFilters).forEach(([key, value]) => {
      if (value && value !== 'all') {
        params.set(key, value)
      }
    })
    
    const newURL = params.toString() ? `?${params.toString()}` : '/cards'
    router.push(newURL)
  }, [router, searchParams])

  // Apply saved filter
  const applySavedFilter = useCallback((filters: Filters) => {
    updateURL(filters)
  }, [updateURL])

  // Handle save filter
  const handleSaveFilter = useCallback((name: string, filters: Filters) => {
    saveFilter(name, filters)
  }, [saveFilter])

  // Trigger search when filters change
  useEffect(() => {
    const filters = getFiltersFromURL()
    search(filters)
  }, [searchParams, search])



  // Fetch filter options
  const fetchFilterOptions = async () => {
    if (!isSupabaseConfigured) return

    try {
      const [fileTypeData, brandData, categoryData, statusData] = await Promise.all([
        supabase.from('files').select('file_type').not('file_type', 'is', null),
        supabase.from('files').select('brand').not('brand', 'is', null),
        supabase.from('files').select('furniture_type').not('furniture_type', 'is', null),
        supabase.from('files').select('status').not('status', 'is', null)
      ])

      setFileTypes(Array.from(new Set(fileTypeData.data?.map(f => f.file_type) || [])).sort())
      setBrands(Array.from(new Set(brandData.data?.map(f => f.brand) || [])).sort())
      setCategories(Array.from(new Set(categoryData.data?.map(f => f.furniture_type) || [])).sort())
      setStatuses(Array.from(new Set(statusData.data?.map(f => f.status) || [])).sort())
    } catch (err) {
      console.error('Error fetching filter options:', err)
    }
  }

  // Handle image error
  const handleImageError = (sha256: string) => {
    setImageError(prev => new Set(prev).add(sha256))
  }

  // Keyboard navigation
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Command palette takes precedence
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      setCommandPaletteOpen(true)
      return
    }

    if (files.length === 0) return

    switch (e.key) {
      case '/':
        e.preventDefault()
        searchRef.current?.focus()
        break
      case 'f':
        if (e.ctrlKey || e.metaKey) return
        e.preventDefault()
        // Focus More... button (handled by PopoverTrigger)
        break
      case 's':
        if (e.ctrlKey || e.metaKey) return
        e.preventDefault()
        // Save filter shortcut (handled by SaveFilterDialog)
        break
      case 'ArrowLeft':
        e.preventDefault()
        const prevIndex = focusedIndex > 0 ? focusedIndex - 1 : files.length - 1
        setFocusedIndex(prevIndex)
        prefetchOnFocus(files[prevIndex])
        break
      case 'ArrowRight':
        e.preventDefault()
        const nextIndex = focusedIndex < files.length - 1 ? focusedIndex + 1 : 0
        setFocusedIndex(nextIndex)
        prefetchOnFocus(files[nextIndex])
        break
      case 'Enter':
        e.preventDefault()
        if (focusedIndex >= 0 && focusedIndex < files.length) {
          openDrawer(focusedIndex)
        }
        break
      case 'c':
        if (e.ctrlKey || e.metaKey) return
        e.preventDefault()
        if (focusedIndex >= 0 && focusedIndex < files.length) {
          const file = files[focusedIndex]
          if (file.source_url) {
            navigator.clipboard.writeText(file.source_url)
          }
        }
        break
    }
  }, [files, focusedIndex])

  // Copy URL
  const copyURL = (url: string) => {
    navigator.clipboard.writeText(url)
    addToast('URL copied to clipboard', 'success')
  }

  // Open drawer
  const openDrawer = (fileIndex: number) => {
    setDrawerFileIndex(fileIndex)
    setCurrentDrawerFile(files[fileIndex])
    setDrawerOpen(true)
  }

  // Close drawer
  const closeDrawer = () => {
    setDrawerOpen(false)
    setDrawerFileIndex(-1)
    setCurrentDrawerFile(null)
  }

  // Navigate drawer
  const navigateDrawer = (direction: 'prev' | 'next') => {
    if (direction === 'prev' && drawerFileIndex > 0) {
      const newIndex = drawerFileIndex - 1
      setDrawerFileIndex(newIndex)
      setCurrentDrawerFile(files[newIndex])
    } else if (direction === 'next' && drawerFileIndex < files.length - 1) {
      const newIndex = drawerFileIndex + 1
      setDrawerFileIndex(newIndex)
      setCurrentDrawerFile(files[newIndex])
    }
  }

  // Switch format in drawer
  const switchDrawerFormat = (file: File) => {
    setCurrentDrawerFile(file)
  }

  // Command palette functions
  const copyCurrentFileUrl = () => {
    if (currentDrawerFile?.source_url) {
      navigator.clipboard.writeText(currentDrawerFile.source_url)
      addToast('URL copied to clipboard', 'success')
    }
  }

  const clearAllFilters = () => {
    router.push('/cards')
  }

  // Prefetch sibling files when card is focused
  const prefetchSiblingFiles = async (file: File) => {
    if (!file.name) return

    try {
      await supabase
        .from('files')
        .select('*')
        .eq('name', file.name)
        .neq('sha256', file.sha256)
        .in('file_type', ['rvt', 'skp', 'dwg', 'dxf'])
        .limit(5)
    } catch (err) {
      // Silent fail for prefetch
    }
  }

  // Handle infinite scroll
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current || loading || !pagination.hasNext) return

    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current
    const isNearBottom = scrollTop + clientHeight >= scrollHeight - 100 // 100px threshold

    if (isNearBottom) {
      const filters = getFiltersFromURL()
      loadMore(filters)
    }
  }, [loading, pagination.hasNext, loadMore])

  // Effects
  useEffect(() => {
    fetchFilterOptions()
  }, [])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown, files])

  // Add scroll listener for infinite scroll
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (scrollContainer) {
      scrollContainer.addEventListener('scroll', handleScroll)
      return () => scrollContainer.removeEventListener('scroll', handleScroll)
    }
  }, [handleScroll])

  useEffect(() => {
    if (focusedIndex >= 0 && cardRefs.current[focusedIndex]) {
      cardRefs.current[focusedIndex]?.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      })
      
      // Prefetch sibling files for instant drawer open
      if (focusedIndex < files.length) {
        prefetchSiblingFiles(files[focusedIndex])
      }
    }
  }, [focusedIndex, files])

  // Check if database is configured
  if (!isSupabaseConfigured) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-amber-600 bg-amber-50 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Configuration Required</h3>
            <p className="text-sm">
              Supabase environment variables are not configured. Please set the following in your Vercel environment:
            </p>
            <ul className="text-sm mt-2 space-y-1">
              <li>• <code className="bg-gray-100 px-1 rounded">NEXT_PUBLIC_SUPABASE_URL</code></li>
              <li>• <code className="bg-gray-100 px-1 rounded">NEXT_PUBLIC_SUPABASE_ANON_KEY</code></li>
            </ul>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-red-600 bg-red-50 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Database Connection Error</h3>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  const filters = getFiltersFromURL()

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="max-w-4xl mx-auto p-6">
          <h1 className="text-2xl font-bold mb-6">Files</h1>
          
          {/* Centered Search */}
          <div className="max-w-md mx-auto mb-6">
            <label htmlFor="search-input" className="sr-only">Search files</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" aria-hidden="true" />
              <Input
                id="search-input"
                ref={searchRef}
                placeholder="Search files, brands, types…"
                value={filters.q}
                onChange={(e) => updateURL({ q: e.target.value })}
                className="pl-10 focus-ring"
                aria-describedby="search-help"
              />
            </div>
            <div id="search-help" className="sr-only">
              Press / to focus search, use arrow keys to navigate results, Enter to open file details
            </div>
          </div>

          {/* Saved Filter Chips */}
          <SavedFilterChips
            savedFilters={savedFilters}
            onApplyFilter={applySavedFilter}
            onDeleteFilter={deleteFilter}
            currentFilters={filters}
          />

          {/* Facet Chips */}
          <div className="flex items-center justify-center gap-2 mb-6" role="group" aria-label="Filter options">
            <Select value={filters.type} onValueChange={(value) => updateURL({ type: value })}>
              <SelectTrigger className="w-auto focus-ring">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {fileTypes.map(type => (
                  <SelectItem key={type} value={type}>{type}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filters.brand} onValueChange={(value) => updateURL({ brand: value })}>
              <SelectTrigger className="w-auto focus-ring">
                <SelectValue placeholder="Brand" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Brands</SelectItem>
                {brands.map(brand => (
                  <SelectItem key={brand} value={brand}>{brand}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filters.cat} onValueChange={(value) => updateURL({ cat: value })}>
              <SelectTrigger className="w-auto focus-ring">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map(cat => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <SaveFilterDialog
              ref={saveFilterDialogRef}
              currentFilters={filters}
              onSaveFilter={handleSaveFilter}
              isCurrentFilterSaved={isCurrentFilterSaved(filters)}
            >
              <Button
                variant="outline"
                size="sm"
                className="focus-ring"
                disabled={isCurrentFilterSaved(filters)}
                title={isCurrentFilterSaved(filters) ? "Filter already saved" : "Save current filter set"}
              >
                <Star className="h-4 w-4" />
              </Button>
            </SaveFilterDialog>

            <Popover>
              <PopoverTrigger asChild>
                <Button ref={moreFiltersRef} variant="outline" size="sm" className="focus-ring">
                  More…
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Status</label>
                    <Select value={filters.status} onValueChange={(value) => updateURL({ status: value })}>
                      <SelectTrigger className="focus-ring">
                        <SelectValue placeholder="All Status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Status</SelectItem>
                        {statuses.map(status => (
                          <SelectItem key={status} value={status}>{status}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label htmlFor="min-size" className="text-sm font-medium">Min Size (MB)</label>
                      <Input
                        id="min-size"
                        type="number"
                        placeholder="0"
                        value={filters.min}
                        onChange={(e) => updateURL({ min: e.target.value })}
                        className="focus-ring"
                      />
                    </div>
                    <div>
                      <label htmlFor="max-size" className="text-sm font-medium">Max Size (MB)</label>
                      <Input
                        id="max-size"
                        type="number"
                        placeholder="∞"
                        value={filters.max}
                        onChange={(e) => updateURL({ max: e.target.value })}
                        className="focus-ring"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Sort By</label>
                    <Select value={filters.sort} onValueChange={(value) => updateURL({ sort: value })}>
                      <SelectTrigger className="focus-ring">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="created_at">Date Created</SelectItem>
                        <SelectItem value="name">Name</SelectItem>
                        <SelectItem value="brand">Brand</SelectItem>
                        <SelectItem value="size_bytes">Size</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </div>

             {/* Content */}
       <div 
         ref={scrollContainerRef}
         className="max-w-7xl mx-auto p-6 h-[calc(100vh-200px)] overflow-y-auto"
       >
                   {/* Loading State */}
          {loading && files.length === 0 && (
            <FileGridSkeleton />
          )}

                   {/* Files Grid */}
          {files.length > 0 && (
            <VirtualizedGrid
              files={files}
              focusedIndex={focusedIndex}
              imageError={imageError}
              onCardClick={openDrawer}
              onCardFocus={(index) => {
                setFocusedIndex(index)
                prefetchOnHover(files[index])
              }}
              onImageError={handleImageError}
              onCopyURL={copyURL}
              cardRefs={cardRefs}
              loading={loading}
            />
          )}

         {/* Pagination Pill */}
         {pagination.totalPages > 1 && (
           <div className="flex justify-center mt-6 mb-4">
             <Badge variant="secondary" className="px-3 py-1">
               Page {pagination.page} of {pagination.totalPages}
               {pagination.totalCount > 0 && (
                 <span className="ml-2 text-muted-foreground">
                   ({pagination.totalCount} files)
                 </span>
               )}
             </Badge>
           </div>
         )}

         {/* Loading More Indicator */}
         {loading && files.length > 0 && (
           <div className="text-center py-4">
             <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
             <div className="text-sm text-muted-foreground mt-2">Loading more...</div>
           </div>
         )}

         {/* No Results */}
         {!loading && files.length === 0 && (
           <div className="text-center py-12">
             <div className="text-muted-foreground">No files found matching your criteria</div>
             <Button 
               variant="outline" 
               className="mt-4"
               onClick={() => router.push('/cards')}
             >
               Clear Filters
             </Button>
           </div>
         )}
       </div>

             {/* File Details Drawer */}
       <FileDetailsDrawer
         file={currentDrawerFile}
         isOpen={drawerOpen}
         onClose={closeDrawer}
         onNavigate={navigateDrawer}
         hasPrev={drawerFileIndex > 0}
         hasNext={drawerFileIndex < files.length - 1}
         imageError={imageError}
         onImageError={handleImageError}
         onSwitchFormat={switchDrawerFormat}
       />

               {/* Command Palette */}
        <CommandPalette
          isOpen={commandPaletteOpen}
          onClose={() => setCommandPaletteOpen(false)}
          context={{
            drawerOpen,
            currentFile: currentDrawerFile,
            hasPrevFile: drawerFileIndex > 0,
            hasNextFile: drawerFileIndex < files.length - 1,
            searchRef,
            moreFiltersRef,
            onNavigateDrawer: navigateDrawer,
            onCopyCurrentFileUrl: copyCurrentFileUrl,
            onClearFilters: clearAllFilters,
            onSaveFilter: () => {
              saveFilterDialogRef.current?.openDialog()
            },
            isCurrentFilterSaved: isCurrentFilterSaved(filters)
          }}
        />

       {/* Performance Monitor */}
       <PerformanceMonitor 
         enabled={shouldMonitorPerformance}
         showDetails={process.env.NODE_ENV === 'development'}
       />
     </div>
   )
 }
