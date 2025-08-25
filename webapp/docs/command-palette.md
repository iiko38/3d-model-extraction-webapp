# Command Palette (⌘K)

A powerful command palette that provides quick access to common actions throughout the application.

## Overview

The command palette is a modal interface that can be opened with `⌘K` (or `Ctrl+K` on Windows/Linux) and provides context-aware actions based on the current state of the application.

## Features

- **Context-Aware**: Actions change based on whether the drawer is open, which file is active, etc.
- **Keyboard Navigation**: Full keyboard support with arrow keys, Enter to execute, Escape to close
- **Search**: Filter commands by typing
- **Categories**: Commands are organized into logical groups
- **Shortcuts**: Visual display of keyboard shortcuts for each action

## Opening the Command Palette

- **Keyboard**: Press `⌘K` (Mac) or `Ctrl+K` (Windows/Linux)
- **Escape**: Press `Escape` to close

## Available Commands

### Navigation & Search
- **Focus search** (`⌘S`) - Focus the main search input
- **Open More filters** (`⌘F`) - Open the advanced filters popover
- **Clear all filters** (`⌘K`) - Reset all filters to default

### File Actions (when drawer is open)
- **Copy current file URL** (`⌘C`) - Copy the source URL of the current file
- **Previous file** (`←`) - Navigate to the previous file in results
- **Next file** (`→`) - Navigate to the next file in results

### Admin
- **Admin: New upload** (`⌘U`) - Navigate to the admin dashboard

### Settings
- **Toggle theme** (`⌘T`) - Switch between light and dark themes (future feature)

## Context Awareness

The command palette intelligently shows different actions based on the current context:

### When Drawer is Closed
- Basic navigation commands
- Search and filter actions
- Admin actions

### When Drawer is Open
- All basic commands
- File-specific actions (copy URL, navigate between files)
- Previous/Next file navigation (only shown if available)

## Keyboard Shortcuts

| Action | Mac | Windows/Linux |
|--------|-----|---------------|
| Open Command Palette | `⌘K` | `Ctrl+K` |
| Close Command Palette | `Escape` | `Escape` |
| Navigate Commands | `↑↓` | `↑↓` |
| Execute Command | `Enter` | `Enter` |
| Focus Search | `⌘S` | `Ctrl+S` |
| Open Filters | `⌘F` | `Ctrl+F` |
| Clear Filters | `⌘K` | `Ctrl+K` |
| Copy File URL | `⌘C` | `Ctrl+C` |
| Previous File | `←` | `←` |
| Next File | `→` | `→` |
| Admin Upload | `⌘U` | `Ctrl+U` |
| Toggle Theme | `⌘T` | `Ctrl+T` |

## Usage Examples

### Quick Search
1. Press `⌘K`
2. Type "search" or "focus"
3. Press `Enter` to focus the search input

### File Navigation
1. Open a file drawer
2. Press `⌘K`
3. Type "next" or "previous"
4. Press `Enter` to navigate

### Copy File URL
1. Open a file drawer
2. Press `⌘K`
3. Type "copy" or "url"
4. Press `Enter` to copy the URL

### Clear Filters
1. Press `⌘K`
2. Type "clear" or "reset"
3. Press `Enter` to clear all filters

## Technical Implementation

### Component Structure
- `CommandPalette.tsx` - Main component
- Uses `cmdk` library for command handling
- Context-aware action generation
- Keyboard event handling

### Integration
- Integrated into the main cards page
- Receives context from parent component
- Handles all keyboard shortcuts
- Manages modal state

### Context Props
```typescript
interface CommandPaletteContext {
  drawerOpen: boolean
  currentFile: File | null
  hasPrevFile: boolean
  hasNextFile: boolean
  searchRef: React.RefObject<HTMLInputElement>
  moreFiltersRef: React.RefObject<HTMLButtonElement>
  onNavigateDrawer: (direction: 'prev' | 'next') => void
  onCopyCurrentFileUrl: () => void
  onClearFilters: () => void
}
```

## Future Enhancements

1. **More Commands**: Add additional context-aware actions
2. **Custom Shortcuts**: Allow users to customize keyboard shortcuts
3. **Command History**: Remember recently used commands
4. **Plugin System**: Allow third-party commands
5. **Voice Commands**: Voice-activated command execution

## Accessibility

- Full keyboard navigation support
- Screen reader compatible
- High contrast mode support
- Focus management
- ARIA labels and descriptions

The command palette provides a powerful and intuitive way to navigate and interact with the application, making it feel more like a native desktop application.
