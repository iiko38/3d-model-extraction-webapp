# Performance Guardrails Implementation

This document outlines the performance optimizations implemented to ensure the application remains fast and responsive even with large datasets (thousands of files).

## Overview

The performance guardrails include:
- **Virtualized Grid**: Efficient rendering for >200 items
- **Lazy Loading**: Images load only when needed
- **Prefetching**: Drawer data loads on card focus/hover
- **Request Abortion**: Stale fetches are cancelled
- **Performance Monitoring**: Real-time metrics tracking

## 1. Virtualized Grid (`VirtualizedGrid.tsx`)

### Purpose
Prevents layout shift and improves performance when displaying large datasets by only rendering visible items.

### Implementation
- **Threshold**: Virtualization activates when >200 items
- **Buffer**: 5 items rendered outside viewport for smooth scrolling
- **Responsive**: Adapts grid columns based on screen size
- **Height Calculation**: Fixed item height (280px) for predictable layout

### Key Features
```typescript
const VIRTUALIZATION_THRESHOLD = 200
const BUFFER_SIZE = 5
const ITEM_HEIGHT = 280

// Calculate visible range
const startIndex = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - BUFFER_SIZE)
const endIndex = Math.min(files.length, Math.ceil((scrollTop + containerHeight) / ITEM_HEIGHT) + BUFFER_SIZE)
```

### Benefits
- **Memory**: Only ~20-30 DOM nodes instead of thousands
- **Performance**: Smooth scrolling at 60fps
- **Layout**: No layout shift during scrolling
- **Responsive**: Works across all screen sizes

## 2. Lazy Loading & Content Visibility

### Image Lazy Loading
All images use `loading="lazy"` and `content-visibility: auto`:

```typescript
<Image
  src={file.thumbnail_url}
  alt={file.name || `3D Model - ${file.file_type}`}
  fill
  className="object-cover"
  loading="lazy"
  style={{ contentVisibility: 'auto' }}
  unoptimized
/>
```

### Benefits
- **Bandwidth**: Images load only when needed
- **Performance**: Reduces initial page load time
- **Memory**: Off-screen images don't consume resources
- **Smooth Scrolling**: No image loading delays

## 3. Prefetching System (`usePrefetch.ts`)

### Purpose
Preloads drawer data when users hover or focus on cards, making drawer opening feel instant.

### Implementation
```typescript
const prefetchOnHover = useCallback((file: File) => {
  // Clear any existing timeout
  if (prefetchTimeoutRef.current) {
    clearTimeout(prefetchTimeoutRef.current)
  }
  
  // Prefetch immediately on hover
  prefetchSiblingFiles(file)
}, [prefetchSiblingFiles])
```

### Features
- **Cache**: 5-minute cache for prefetched data
- **Debouncing**: Prevents excessive requests
- **Smart Timing**: Immediate on hover, delayed on focus
- **Error Handling**: Graceful fallback on failures

### Cache Strategy
```typescript
const PREFETCH_CACHE_DURATION = 5 * 60 * 1000 // 5 minutes
const cacheKey = `${file.product_slug}-${file.brand}`
```

## 4. Request Abortion (`useHybridSearch.ts`)

### Purpose
Cancels stale requests when filters change, preventing race conditions and unnecessary network traffic.

### Implementation
```typescript
const abortControllerRef = useRef<AbortController | null>(null)

const simpleSearch = useCallback(async (params: SearchParams, page: number = 1) => {
  // Abort any ongoing request
  if (abortControllerRef.current) {
    abortControllerRef.current.abort()
  }
  
  // Create new abort controller for this request
  abortControllerRef.current = new AbortController()
  
  // ... search logic
}, [])
```

### Benefits
- **Network**: Reduces unnecessary requests
- **Performance**: Prevents UI updates from stale data
- **Memory**: Frees up resources from cancelled requests
- **User Experience**: No flickering from outdated results

## 5. Performance Monitoring (`PerformanceMonitor.tsx`)

### Purpose
Real-time monitoring of application performance metrics to ensure optimal user experience.

### Metrics Tracked
- **FPS**: Frame rate monitoring (target: 55+ FPS)
- **Memory**: JavaScript heap usage (target: <200MB)
- **CPU**: Processing time (target: <10ms)
- **Render Time**: Component render duration

### Implementation
```typescript
// FPS monitoring
const measureFPS = useRef(() => {
  frameCountRef.current++
  const currentTime = performance.now()
  
  if (currentTime - lastTimeRef.current >= 1000) {
    const fps = Math.round((frameCountRef.current * 1000) / (currentTime - lastTimeRef.current))
    setMetrics(prev => ({ ...prev, fps }))
    frameCountRef.current = 0
    lastTimeRef.current = currentTime
  }
  
  animationFrameRef.current = requestAnimationFrame(measureFPS.current)
})
```

### Visual Indicators
- **Green**: Optimal performance
- **Yellow**: Acceptable performance
- **Red**: Performance issues detected

### Activation
- **Development**: Always enabled with detailed view
- **Production**: Enabled when >200 files
- **Configurable**: Can be toggled on/off

## 6. Integration with Main Page

### Virtualized Grid Integration
```typescript
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
```

### Prefetching Integration
```typescript
// Keyboard navigation with prefetching
case 'ArrowLeft':
  e.preventDefault()
  const prevIndex = focusedIndex > 0 ? focusedIndex - 1 : files.length - 1
  setFocusedIndex(prevIndex)
  prefetchOnFocus(files[prevIndex])
  break
```

## 7. Performance Targets

### Success Criteria
- **CPU**: Stays chilled (<10ms processing time)
- **Memory**: Stable usage (<200MB for large datasets)
- **Scrolling**: No jank when scrolling thousands of items
- **FPS**: Maintains 55+ FPS during interactions

### Monitoring Thresholds
```typescript
const getFPSColor = (fps: number) => {
  if (fps >= 55) return 'bg-green-100 text-green-800 border-green-200'
  if (fps >= 45) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
  return 'bg-red-100 text-red-800 border-red-200'
}

const getMemoryColor = (memory: number | null) => {
  if (!memory) return 'bg-gray-100 text-gray-800 border-gray-200'
  if (memory < 100) return 'bg-green-100 text-green-800 border-green-200'
  if (memory < 200) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
  return 'bg-red-100 text-red-800 border-red-200'
}
```

## 8. Browser Support

### Required Features
- **ResizeObserver**: For responsive grid calculations
- **AbortController**: For request cancellation
- **Performance API**: For memory monitoring
- **CSS Grid**: For layout virtualization

### Fallbacks
- **No ResizeObserver**: Grid defaults to standard layout
- **No AbortController**: Requests continue without cancellation
- **No Performance API**: Memory monitoring disabled
- **No CSS Grid**: Falls back to flexbox layout

## 9. Testing Performance

### Development Testing
```bash
# Enable performance monitoring
npm run dev

# Test with large datasets
# Monitor FPS, memory, and CPU usage in browser
```

### Production Testing
```bash
# Build and test performance
npm run build
npm start

# Test with thousands of files
# Verify virtualization and prefetching work correctly
```

### Performance Checklist
- [ ] Virtualization activates at >200 items
- [ ] Smooth scrolling at 60fps
- [ ] Memory usage stays under 200MB
- [ ] Prefetching works on hover/focus
- [ ] Stale requests are aborted
- [ ] Images lazy load correctly
- [ ] Performance monitor shows green indicators

## 10. Future Optimizations

### Potential Enhancements
- **Web Workers**: Move heavy computations off main thread
- **Service Workers**: Cache API responses for offline support
- **Intersection Observer**: More efficient lazy loading
- **WebAssembly**: Performance-critical operations
- **IndexedDB**: Client-side caching for large datasets

### Monitoring Improvements
- **Real User Monitoring**: Collect performance data from users
- **Error Tracking**: Monitor performance-related errors
- **Analytics**: Track performance metrics over time
- **Alerts**: Notify when performance degrades

## Conclusion

The performance guardrails ensure the application remains fast and responsive regardless of dataset size. The combination of virtualization, lazy loading, prefetching, and monitoring provides a robust foundation for handling thousands of files while maintaining excellent user experience.
