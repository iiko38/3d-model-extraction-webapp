'use client'

import { useState, useRef, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Pencil, Check, X } from 'lucide-react'
import { useToast } from '@/components/ui/toast'

interface InlineEditProps {
  value: string
  field: string
  sha256: string
  onUpdate: (field: string, value: string) => void
  isAdmin: boolean
  className?: string
}

export default function InlineEdit({ 
  value, 
  field, 
  sha256, 
  onUpdate, 
  isAdmin, 
  className = '' 
}: InlineEditProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(value)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const { addToast } = useToast()

  useEffect(() => {
    setEditValue(value)
  }, [value])

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const handleEdit = () => {
    if (!isAdmin) return
    setIsEditing(true)
  }

  const handleSave = async () => {
    if (editValue.trim() === value) {
      setIsEditing(false)
      return
    }

    setLoading(true)
    try {
      await onUpdate(field, editValue.trim())
      setIsEditing(false)
      addToast(`${field} updated successfully`, 'success')
    } catch (error) {
      console.error('Update failed:', error)
      addToast(`Failed to update ${field}`, 'error')
      setEditValue(value) // Reset to original value
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditValue(value)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      handleCancel()
    }
  }

  if (!isAdmin) {
    return <span className={className}>{value}</span>
  }

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <Input
          ref={inputRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1"
          disabled={loading}
        />
        <Button
          size="sm"
          variant="ghost"
          onClick={handleSave}
          disabled={loading}
          className="h-8 w-8 p-0"
          aria-label="Save changes"
        >
          <Check className="h-4 w-4" />
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleCancel}
          disabled={loading}
          className="h-8 w-8 p-0"
          aria-label="Cancel changes"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 group">
      <span className={className}>{value}</span>
      <Button
        size="sm"
        variant="ghost"
        onClick={handleEdit}
        className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
        aria-label={`Edit ${field}`}
      >
        <Pencil className="h-3 w-3" />
      </Button>
    </div>
  )
}
