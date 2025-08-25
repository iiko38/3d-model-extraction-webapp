# URL Discipline & Saved Filters Implementation

This document outlines the implementation of URL discipline and saved filters functionality, which keeps filters in the querystring and allows users to save and apply filter sets.

## Overview

The implementation provides:
- **URL Discipline**: All filters are maintained in the URL querystring for shareable links and browser history
- **Saved Filters**: Users can save current filter sets with friendly names and apply them later
- **Filter Chips**: Visual representation of saved filters with one-click application
- **Keyboard Shortcuts**: Quick access to save and apply filters

## 1. URL Discipline

### Implementation
All filter state is synchronized with the URL querystring using Next.js `useSearchParams` and `useRouter`:

```typescript
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
```

### Benefits
- **Shareable Links**: Users can share specific filter combinations via URL
- **Browser History**: Back/forward navigation works with filter changes
- **Bookmarkable**: Specific filter states can be bookmarked
- **Deep Linking**: Direct links to filtered views

## 2. Saved Filters System

### Core Hook (`useSavedFilters.ts`)

The saved filters functionality is encapsulated in a custom hook that manages:
- **localStorage Persistence**: Filters are saved to browser storage
- **CRUD Operations**: Save, load, delete, and check filter existence
- **Cache Management**: Efficient storage and retrieval

```typescript
export function useSavedFilters() {
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([])
  
  // Save current filter set
  const saveFilter = useCallback((name: string, filters: Filters) => {
    const newFilter: SavedFilter = {
      id: Date.now().toString(),
      name,
      filters,
      createdAt: Date.now()
    }
    // ... save to localStorage
  }, [])
  
  // Check if current filters match a saved filter
  const isCurrentFilterSaved = useCallback((currentFilters: Filters) => {
    return savedFilters.some(saved => {
      return Object.keys(currentFilters).every(key => {
        const k = key as keyof Filters
        return saved.filters[k] === currentFilters[k]
      })
    })
  }, [savedFilters])
}
```

### Data Structure
```typescript
interface SavedFilter {
  id: string
  name: string
  filters: Filters
  createdAt: number
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
```

## 3. Saved Filter Chips (`SavedFilterChips.tsx`)

### Features
- **Visual Display**: Shows all saved filters as clickable chips
- **Active State**: Highlights currently applied filter
- **One-Click Apply**: Click to apply filter and scroll to top
- **Delete Functionality**: Remove saved filters with X button
- **Toast Notifications**: User feedback for actions

### Implementation
```typescript
export default function SavedFilterChips({
  savedFilters,
  onApplyFilter,
  onDeleteFilter,
  currentFilters
}: SavedFilterChipsProps) {
  const handleApplyFilter = (filter: SavedFilter) => {
    onApplyFilter(filter.filters)
    addToast(`Applied filter: ${filter.name}`, 'success')
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  
  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {savedFilters.map((filter) => (
        <Badge
          key={filter.id}
          variant={isActive ? "default" : "outline"}
          className="cursor-pointer hover:bg-primary/90 transition-colors"
          onClick={() => handleApplyFilter(filter)}
        >
          <Star className="h-3 w-3 mr-1" />
          {filter.name}
          <Button onClick={(e) => {
            e.stopPropagation()
            handleDeleteFilter(filter.id, filter.name)
          }}>
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}
    </div>
  )
}
```

## 4. Save Filter Dialog (`SaveFilterDialog.tsx`)

### Features
- **Modal Dialog**: Clean interface for naming and saving filters
- **Current Filter Preview**: Shows what will be saved
- **Validation**: Ensures filter name is provided
- **Keyboard Support**: Enter to save, Escape to cancel
- **External Trigger**: Can be opened programmatically

### Implementation
```typescript
const SaveFilterDialog = forwardRef<SaveFilterDialogRef, SaveFilterDialogProps>(({
  currentFilters,
  onSaveFilter,
  isCurrentFilterSaved,
  children
}, ref) => {
  const [isOpen, setIsOpen] = useState(false)
  const [filterName, setFilterName] = useState('')
  
  // Expose open method for external triggers
  useImperativeHandle(ref, () => ({
    openDialog: () => {
      if (!isCurrentFilterSaved) {
        setIsOpen(true)
      }
    }
  }), [isCurrentFilterSaved])
  
  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Save Filter</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="filter-name">Filter Name</Label>
            <Input
              placeholder="e.g., Large Revit Files, Ikea Chairs..."
              value={filterName}
              onChange={(e) => setFilterName(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
            />
          </div>
          
          <div className="text-sm text-muted-foreground">
            <p className="font-medium mb-2">Current filters:</p>
            {/* Display current filter state */}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
})
```

## 5. Integration with Main Page

### Save Filter Button
A star button (⭐) is added to the filter controls:
```typescript
<SaveFilterDialog
  ref={saveFilterDialogRef}
  currentFilters={filters}
  onSaveFilter={handleSaveFilter}
  isCurrentFilterSaved={isCurrentFilterSaved(filters)}
>
  <Button
    variant="outline"
    size="sm"
    disabled={isCurrentFilterSaved(filters)}
    title={isCurrentFilterSaved(filters) ? "Filter already saved" : "Save current filter set"}
  >
    <Star className="h-4 w-4" />
  </Button>
</SaveFilterDialog>
```

### Saved Filter Chips Display
```typescript
<SavedFilterChips
  savedFilters={savedFilters}
  onApplyFilter={applySavedFilter}
  onDeleteFilter={deleteFilter}
  currentFilters={filters}
/>
```

## 6. Keyboard Shortcuts

### Command Palette Integration
The command palette includes save filter functionality:
```typescript
{
  id: 'save-filter',
  name: context.isCurrentFilterSaved ? 'Filter already saved' : 'Save current filter',
  shortcut: ['S'],
  icon: <Star className="h-4 w-4" />,
  action: () => {
    if (context.onSaveFilter && !context.isCurrentFilterSaved) {
      context.onSaveFilter()
    }
    onClose()
  },
  keywords: ['save', 'filter', 'star', 'bookmark'],
  category: 'Navigation'
}
```

### Keyboard Navigation
- **S**: Save current filter (when not already saved)
- **⌘K**: Open command palette with save filter option
- **Enter**: Save filter in dialog
- **Escape**: Cancel save filter dialog

## 7. User Experience Features

### Visual Feedback
- **Active State**: Saved filter chips show which filter is currently applied
- **Disabled State**: Save button is disabled when current filter is already saved
- **Toast Notifications**: Success/error messages for all actions
- **Smooth Scrolling**: Automatic scroll to top when applying filters

### Accessibility
- **ARIA Labels**: Proper labeling for screen readers
- **Keyboard Navigation**: Full keyboard support
- **Focus Management**: Proper focus handling in dialogs
- **Screen Reader Announcements**: Toast notifications for actions

### Error Handling
- **localStorage Errors**: Graceful fallback if storage is unavailable
- **Validation**: Filter name validation
- **Network Errors**: Error handling for filter operations
- **Duplicate Prevention**: Prevents saving duplicate filters

## 8. Storage Strategy

### localStorage Structure
```json
{
  "saved-filters": [
    {
      "id": "1703123456789",
      "name": "Large Revit Files",
      "filters": {
        "q": "",
        "type": "rvt",
        "brand": "all",
        "cat": "all",
        "status": "all",
        "min": "50",
        "max": "",
        "sort": "size_bytes"
      },
      "createdAt": 1703123456789
    }
  ]
}
```

### Storage Limits
- **Browser Limit**: Respects localStorage size limits
- **Filter Count**: No hard limit, but UI suggests reasonable number
- **Data Size**: Each filter is ~200 bytes, allowing hundreds of saved filters

## 9. Performance Considerations

### Optimization
- **Debounced Updates**: URL updates are debounced to prevent excessive navigation
- **Memoized Functions**: Callbacks are memoized to prevent unnecessary re-renders
- **Efficient Storage**: Minimal data stored per filter
- **Lazy Loading**: Filter chips only render when needed

### Memory Management
- **Cleanup**: Proper cleanup of event listeners and refs
- **State Management**: Efficient state updates
- **Storage Cleanup**: Automatic cleanup of invalid stored data

## 10. Testing Scenarios

### URL Discipline
- [ ] Filter changes update URL
- [ ] URL changes update filters
- [ ] Browser back/forward works
- [ ] Direct URL access works
- [ ] Shareable links work

### Saved Filters
- [ ] Save filter with name
- [ ] Apply saved filter
- [ ] Delete saved filter
- [ ] Prevent duplicate saves
- [ ] Persist across sessions
- [ ] Handle storage errors

### User Experience
- [ ] Visual feedback for actions
- [ ] Keyboard shortcuts work
- [ ] Accessibility features
- [ ] Error handling
- [ ] Performance with many filters

## 11. Future Enhancements

### Potential Improvements
- **Filter Categories**: Organize saved filters into categories
- **Filter Sharing**: Share saved filters between users
- **Filter Import/Export**: Backup and restore filter sets
- **Filter Analytics**: Track most used filters
- **Smart Suggestions**: Suggest filter names based on content
- **Filter Templates**: Pre-defined filter templates

### Advanced Features
- **Filter Combinations**: Save complex filter logic
- **Filter Scheduling**: Auto-apply filters at certain times
- **Filter Notifications**: Notify when new items match saved filters
- **Filter Collaboration**: Team-shared filter sets

## Conclusion

The URL discipline and saved filters implementation provides a robust, user-friendly system for managing filter states. The combination of URL synchronization, persistent storage, and intuitive UI creates a powerful tool for users to organize and quickly access their preferred filter combinations.

The implementation follows best practices for accessibility, performance, and user experience, while maintaining clean, maintainable code that can be easily extended with additional features.
