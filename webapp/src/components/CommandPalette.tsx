'use client'

import { useState, useEffect, useCallback } from 'react'
import { Command } from 'cmdk'
import { Search, Filter, X, Copy, ChevronLeft, ChevronRight, Upload, Sun, Moon, Settings, Star } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useToast } from '@/components/ui/toast'

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  // Context from parent components
  context: {
    drawerOpen: boolean
    currentFile: any | null
    hasPrevFile: boolean
    hasNextFile: boolean
    searchRef: React.RefObject<HTMLInputElement>
    moreFiltersRef: React.RefObject<HTMLButtonElement>
    onNavigateDrawer: (direction: 'prev' | 'next') => void
    onCopyCurrentFileUrl: () => void
    onClearFilters: () => void
    onSaveFilter?: () => void
    isCurrentFilterSaved?: boolean
  }
}

interface CommandAction {
  id: string
  name: string
  shortcut?: string[]
  icon: React.ReactNode
  action: () => void
  keywords: string[]
  category: string
}

export default function CommandPalette({ isOpen, onClose, context }: CommandPaletteProps) {
  const [search, setSearch] = useState('')
  const router = useRouter()
  const { addToast } = useToast()

  // Generate actions based on context
  const getActions = useCallback((): CommandAction[] => {
    const actions: CommandAction[] = [
      // Navigation & Search
      {
        id: 'focus-search',
        name: 'Focus search',
        shortcut: ['⌘', 'S'],
        icon: <Search className="h-4 w-4" />,
        action: () => {
          context.searchRef.current?.focus()
          onClose()
        },
        keywords: ['search', 'find', 'query', 'focus'],
        category: 'Navigation'
      },
      {
        id: 'open-filters',
        name: 'Open More filters',
        shortcut: ['⌘', 'F'],
        icon: <Filter className="h-4 w-4" />,
        action: () => {
          context.moreFiltersRef.current?.click()
          onClose()
        },
        keywords: ['filter', 'more', 'advanced', 'options'],
        category: 'Navigation'
      },
      {
        id: 'clear-filters',
        name: 'Clear all filters',
        shortcut: ['⌘', 'K'],
        icon: <X className="h-4 w-4" />,
        action: () => {
          context.onClearFilters()
          onClose()
        },
        keywords: ['clear', 'reset', 'remove', 'filters'],
        category: 'Navigation'
      },
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
      },
    ]

    // File navigation (only if drawer is open)
    if (context.drawerOpen && context.currentFile) {
      actions.push(
        {
          id: 'copy-file-url',
          name: 'Copy current file URL',
          shortcut: ['⌘', 'C'],
          icon: <Copy className="h-4 w-4" />,
          action: () => {
            context.onCopyCurrentFileUrl()
            onClose()
          },
          keywords: ['copy', 'url', 'link', 'share'],
          category: 'File'
        }
      )

      if (context.hasPrevFile) {
        actions.push({
          id: 'previous-file',
          name: 'Previous file',
          shortcut: ['←'],
          icon: <ChevronLeft className="h-4 w-4" />,
          action: () => {
            context.onNavigateDrawer('prev')
            onClose()
          },
          keywords: ['previous', 'back', 'prev', 'left'],
          category: 'File'
        })
      }

      if (context.hasNextFile) {
        actions.push({
          id: 'next-file',
          name: 'Next file',
          shortcut: ['→'],
          icon: <ChevronRight className="h-4 w-4" />,
          action: () => {
            context.onNavigateDrawer('next')
            onClose()
          },
          keywords: ['next', 'forward', 'right'],
          category: 'File'
        })
      }
    }

    // Admin actions
    actions.push({
      id: 'admin-upload',
      name: 'Admin: New upload',
      shortcut: ['⌘', 'U'],
      icon: <Upload className="h-4 w-4" />,
      action: () => {
        router.push('/admin')
        onClose()
      },
      keywords: ['admin', 'upload', 'new', 'add'],
      category: 'Admin'
    })

    // Theme toggle (optional)
    actions.push({
      id: 'toggle-theme',
      name: 'Toggle theme',
      shortcut: ['⌘', 'T'],
      icon: <Sun className="h-4 w-4" />,
      action: () => {
        // TODO: Implement theme toggle
        console.log('Toggle theme')
        onClose()
      },
      keywords: ['theme', 'dark', 'light', 'mode'],
      category: 'Settings'
    })

    return actions
  }, [context, onClose, router])

  const actions = getActions()

  // Group actions by category
  const groupedActions = actions.reduce((acc, action) => {
    if (!acc[action.category]) {
      acc[action.category] = []
    }
    acc[action.category].push(action)
    return acc
  }, {} as Record<string, CommandAction[]>)

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // ⌘K to open command palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        if (!isOpen) {
          // Open command palette
          setSearch('')
        }
      }

      // Escape to close
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault()
        onClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 z-50 bg-black/50 flex items-start justify-center pt-[20vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div className="w-full max-w-2xl mx-4">
        <Command className="bg-white radius-card shadow-2xl border border-gray-200 motion-normal">
          <div className="flex items-center border-b border-gray-200 px-4 py-3">
            <Search className="h-4 w-4 text-gray-400 mr-3" aria-hidden="true" />
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Search commands..."
              className="flex-1 outline-none text-sm focus-ring"
              aria-label="Search commands"
            />
            <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border bg-gray-100 px-1.5 font-mono text-xs font-medium text-gray-600" aria-label="Keyboard shortcut">
              <span className="text-xs">⌘</span>K
            </kbd>
          </div>
          
          <Command.List className="max-h-96 overflow-y-auto p-2">
            {Object.entries(groupedActions).map(([category, categoryActions]) => (
              <div key={category}>
                <Command.Group heading={category} className="px-2 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {categoryActions.map((action) => (
                                         <Command.Item
                       key={action.id}
                       value={`${action.name} ${action.keywords.join(' ')}`}
                       onSelect={action.action}
                       className="flex items-center gap-3 px-3 py-2 text-sm rounded-md cursor-pointer motion-fast hover:bg-gray-100 data-[selected=true]:bg-gray-100 focus-ring"
                       aria-label={action.name}
                     >
                      <div className="flex-shrink-0 text-gray-500">
                        {action.icon}
                      </div>
                      <div className="flex-1">
                        <span className="font-medium">{action.name}</span>
                      </div>
                      {action.shortcut && (
                        <div className="flex-shrink-0">
                          <kbd className="inline-flex h-5 select-none items-center gap-1 rounded border bg-gray-100 px-1.5 font-mono text-xs font-medium text-gray-600">
                            {action.shortcut.map((key, index) => (
                              <span key={index}>
                                {key}
                                {index < action.shortcut!.length - 1 && <span className="text-gray-400">+</span>}
                              </span>
                            ))}
                          </kbd>
                        </div>
                      )}
                    </Command.Item>
                  ))}
                </Command.Group>
              </div>
            ))}
            
            {actions.length === 0 && (
              <div className="px-3 py-8 text-center text-sm text-gray-500">
                No commands found.
              </div>
            )}
          </Command.List>
        </Command>
      </div>
    </div>
  )
}
