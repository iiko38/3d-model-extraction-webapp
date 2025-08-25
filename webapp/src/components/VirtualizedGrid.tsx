'use client'

import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import Image from 'next/image'
import { Info, Copy } from 'lucide-react'

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

interface VirtualizedGridProps {
  files: File[]
  focusedIndex: number
  imageError: Set<string>
  onCardClick: (index: number) => void
  onCardFocus: (index: number) => void
  onImageError: (sha256: string) => void
  onCopyURL: (url: string) => void
  cardRefs: React.MutableRefObject<(HTMLDivElement | null)[]>
  loading?: boolean
}

const ITEM_HEIGHT = 280 // Approximate height of each card
const BUFFER_SIZE = 5 // Number of items to render outside viewport
const VIRTUALIZATION_THRESHOLD = 200 // Start virtualizing after this many items

export default function VirtualizedGrid({
  files,
  focusedIndex,
  imageError,
  onCardClick,
  onCardFocus,
  onImageError,
  onCopyURL,
  cardRefs,
  loading = false
}: VirtualizedGridProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [scrollTop, setScrollTop] = useState(0)
  const [containerHeight, setContainerHeight] = useState(0)
  const [containerWidth, setContainerWidth] = useState(0)

  // Calculate grid layout
  const gridConfig = useMemo(() => {
    if (containerWidth < 640) return { cols: 2, gap: 20 }
    if (containerWidth < 768) return { cols: 3, gap: 20 }
    if (containerWidth < 1024) return { cols: 4, gap: 20 }
    if (containerWidth < 1280) return { cols: 5, gap: 20 }
    return { cols: 6, gap: 20 }
  }, [containerWidth])

  // Calculate item width
  const itemWidth = useMemo(() => {
    return (containerWidth - (gridConfig.cols - 1) * gridConfig.gap) / gridConfig.cols
  }, [containerWidth, gridConfig])

  // Calculate total height and rows
  const totalRows = Math.ceil(files.length / gridConfig.cols)
  const totalHeight = totalRows * ITEM_HEIGHT + (totalRows - 1) * gridConfig.gap

  // Calculate visible range
  const startIndex = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - BUFFER_SIZE)
  const endIndex = Math.min(
    files.length,
    Math.ceil((scrollTop + containerHeight) / ITEM_HEIGHT) + BUFFER_SIZE
  )

  // Handle scroll
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop)
  }, [])

  // Handle resize
  const handleResize = useCallback(() => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect()
      setContainerHeight(rect.height)
      setContainerWidth(rect.width)
    }
  }, [])

  // Set up resize observer
  useEffect(() => {
    if (!containerRef.current) return

    handleResize()
    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(containerRef.current)

    return () => resizeObserver.disconnect()
  }, [handleResize])

  // If we have fewer items than threshold, render normally
  if (files.length <= VIRTUALIZATION_THRESHOLD) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 space-grid">
        {files.map((file, index) => (
          <Card 
            key={file.sha256}
            ref={(el) => { cardRefs.current[index] = el }}
            className={`relative overflow-hidden cursor-pointer radius-card motion-normal focus-ring ${
              focusedIndex === index ? 'ring-2 ring-primary shadow-lg' : 'hover:shadow-md'
            }`}
            onClick={() => onCardClick(index)}
            onMouseEnter={() => onCardFocus(index)}
            tabIndex={0}
            role="button"
            aria-label={`${file.name || 'File'}, ${file.brand || 'Unknown'} brand, ${file.file_type || 'Unknown'} format`}
            aria-describedby={`file-title-${file.sha256}`}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onCardClick(index)
              }
            }}
          >
            {/* Thumbnail */}
            <div className="aspect-square bg-muted relative">
              {file.thumbnail_url && !imageError.has(file.sha256) ? (
                <Image
                  src={file.thumbnail_url}
                  alt={file.name || `3D Model - ${file.file_type}`}
                  fill
                  className="object-cover"
                  onError={() => onImageError(file.sha256)}
                  unoptimized
                  loading="lazy"
                  style={{ contentVisibility: 'auto' }}
                />
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center">
                    <div className="text-2xl mb-2">📁</div>
                    <span className="text-xs">{file.file_type?.toUpperCase()}</span>
                  </div>
                </div>
              )}
              
              {/* Hover Actions */}
              <div className="absolute top-2 right-2 opacity-0 hover:opacity-100 transition-opacity">
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="secondary"
                    className="h-6 w-6 p-0 focus-ring"
                    onClick={(e) => {
                      e.stopPropagation()
                      onCardClick(index)
                    }}
                    aria-label={`Inspect ${file.name || 'file'}`}
                    title="Inspect (i)"
                  >
                    <Info className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    className="h-6 w-6 p-0 focus-ring"
                    onClick={(e) => {
                      e.stopPropagation()
                      if (file.product_url || file.source_url) onCopyURL(file.product_url || file.source_url)
                    }}
                    aria-label={`Copy URL for ${file.name || 'file'}`}
                    title="Copy URL (c)"
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              
              {/* Status Dot */}
              <div className="absolute bottom-2 left-2">
                <div 
                  className={`w-2 h-2 rounded-full ${
                    file.status === 'active' ? 'bg-green-500' :
                    file.status === 'pending' ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}
                  aria-label={`Status: ${file.status}`}
                  role="status"
                />
              </div>
            </div>

            {/* Card Content */}
            <CardContent className="card-padding">
              <h3 className="font-medium text-sm truncate mb-1" id={`file-title-${file.sha256}`}>
                {file.name || `File ${file.sha256?.slice(0, 8)}`}
              </h3>
              <p className="text-xs text-muted-foreground truncate" aria-describedby={`file-title-${file.sha256}`}>
                {file.brand || 'Unknown'} · {file.file_type || 'Unknown'}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  // Virtualized rendering for large datasets
  const visibleFiles = files.slice(startIndex, endIndex)
  const offsetY = startIndex * ITEM_HEIGHT

  return (
    <div 
      ref={containerRef}
      className="relative overflow-auto"
      style={{ height: '100%' }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            position: 'absolute',
            top: offsetY,
            left: 0,
            right: 0,
            display: 'grid',
            gridTemplateColumns: `repeat(${gridConfig.cols}, 1fr)`,
            gap: gridConfig.gap,
          }}
        >
          {visibleFiles.map((file, index) => {
            const actualIndex = startIndex + index
            const row = Math.floor(actualIndex / gridConfig.cols)
            const col = actualIndex % gridConfig.cols
            
            return (
              <Card 
                key={file.sha256}
                ref={(el) => { cardRefs.current[actualIndex] = el }}
                className={`relative overflow-hidden cursor-pointer radius-card motion-normal focus-ring ${
                  focusedIndex === actualIndex ? 'ring-2 ring-primary shadow-lg' : 'hover:shadow-md'
                }`}
                style={{
                  height: ITEM_HEIGHT,
                  width: itemWidth,
                }}
                onClick={() => onCardClick(actualIndex)}
                onMouseEnter={() => onCardFocus(actualIndex)}
                tabIndex={0}
                role="button"
                aria-label={`${file.name || 'File'}, ${file.brand || 'Unknown'} brand, ${file.file_type || 'Unknown'} format`}
                aria-describedby={`file-title-${file.sha256}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    onCardClick(actualIndex)
                  }
                }}
              >
                {/* Thumbnail */}
                <div className="aspect-square bg-muted relative">
                  {file.thumbnail_url && !imageError.has(file.sha256) ? (
                    <Image
                      src={file.thumbnail_url}
                      alt={file.name || `3D Model - ${file.file_type}`}
                      fill
                      className="object-cover"
                      onError={() => onImageError(file.sha256)}
                      unoptimized
                      loading="lazy"
                      style={{ contentVisibility: 'auto' }}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground">
                      <div className="text-center">
                        <div className="text-2xl mb-2">📁</div>
                        <span className="text-xs">{file.file_type?.toUpperCase()}</span>
                      </div>
                    </div>
                  )}
                  
                  {/* Hover Actions */}
                  <div className="absolute top-2 right-2 opacity-0 hover:opacity-100 transition-opacity">
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-6 w-6 p-0 focus-ring"
                        onClick={(e) => {
                          e.stopPropagation()
                          onCardClick(actualIndex)
                        }}
                        aria-label={`Inspect ${file.name || 'file'}`}
                        title="Inspect (i)"
                      >
                        <Info className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-6 w-6 p-0 focus-ring"
                        onClick={(e) => {
                          e.stopPropagation()
                          if (file.product_url || file.source_url) onCopyURL(file.product_url || file.source_url)
                        }}
                        aria-label={`Copy URL for ${file.name || 'file'}`}
                        title="Copy URL (c)"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  
                  {/* Status Dot */}
                  <div className="absolute bottom-2 left-2">
                    <div 
                      className={`w-2 h-2 rounded-full ${
                        file.status === 'active' ? 'bg-green-500' :
                        file.status === 'pending' ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      aria-label={`Status: ${file.status}`}
                      role="status"
                    />
                  </div>
                </div>

                {/* Card Content */}
                <CardContent className="card-padding">
                  <h3 className="font-medium text-sm truncate mb-1" id={`file-title-${file.sha256}`}>
                    {file.name || `File ${file.sha256?.slice(0, 8)}`}
                  </h3>
                  <p className="text-xs text-muted-foreground truncate" aria-describedby={`file-title-${file.sha256}`}>
                    {file.brand || 'Unknown'} · {file.file_type || 'Unknown'}
                  </p>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}
