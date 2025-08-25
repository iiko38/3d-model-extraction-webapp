'use client'

import { useState, useEffect, useRef } from 'react'
import { supabase } from '@/lib/supabase'
import Image from 'next/image'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { X, ExternalLink, Copy, Download, ChevronLeft, ChevronRight, AlertCircle, CheckCircle, XCircle } from 'lucide-react'
import { useLinkHealth } from '@/hooks/useLinkHealth'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import FileDrawerSkeleton from '@/components/FileDrawerSkeleton'
import { useToast } from '@/components/ui/toast'
import { useAdmin } from '@/hooks/useAdmin'
import InlineEdit from '@/components/InlineEdit'
import AdminActions from '@/components/AdminActions'
import IssueTriagePanel from '@/components/IssueTriagePanel'

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

interface FileDetailsDrawerProps {
  file: File | null
  isOpen: boolean
  onClose: () => void
  onNavigate: (direction: 'prev' | 'next') => void
  hasPrev: boolean
  hasNext: boolean
  imageError: Set<string>
  onImageError: (sha256: string) => void
  onSwitchFormat?: (file: File) => void
}

export default function FileDetailsDrawer({
  file,
  isOpen,
  onClose,
  onNavigate,
  hasPrev,
  hasNext,
  imageError,
  onImageError,
  onSwitchFormat
}: FileDetailsDrawerProps) {
  const { addToast } = useToast()
  const { isAdmin } = useAdmin()
  const [siblingFiles, setSiblingFiles] = useState<File[]>([])
  const [selectedFormat, setSelectedFormat] = useState<string>('')
  const [showMeta, setShowMeta] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)
  const [reportIssue, setReportIssue] = useState(false)
  const [issueText, setIssueText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentFile, setCurrentFile] = useState<File | null>(file)
  
  const drawerRef = useRef<HTMLDivElement>(null)
  
  // Link health check
  const linkHealthStatus = useLinkHealth(currentFile?.source_url || null)

  // Generate product slug from name
  const generateProductSlug = (name: string): string => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim()
  }

  // Fetch sibling files (same product, different formats)
  const fetchSiblingFiles = async (currentFile: File) => {
    if (!currentFile.name || !currentFile.brand) return

    setIsLoading(true)
    const productSlug = currentFile.product_slug || generateProductSlug(currentFile.name)

    try {
      const { data } = await supabase
        .from('files')
        .select('*')
        .eq('brand', currentFile.brand)
        .neq('sha256', currentFile.sha256)
        .in('file_type', ['rvt', 'skp', 'dwg', 'dxf'])
        .order('file_type')

      // Filter by product slug (client-side for now)
      const siblings = data?.filter(f => {
        const siblingSlug = f.product_slug || generateProductSlug(f.name || '')
        return siblingSlug === productSlug
      }) || []

      setSiblingFiles(siblings)
    } catch (err) {
      console.error('Error fetching sibling files:', err)
    } finally {
      setIsLoading(false)
    }
  }

  // Handle format switching
  const switchFormat = (format: string) => {
    const sibling = siblingFiles.find(f => f.file_type === format)
    if (sibling && onSwitchFormat) {
      onSwitchFormat(sibling)
      setSelectedFormat(format)
    }
  }

  // Copy to clipboard
  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(type)
      addToast(`${type === 'url' ? 'URL' : 'SHA256'} copied to clipboard`, 'success')
      setTimeout(() => setCopied(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
      addToast('Failed to copy to clipboard', 'error')
    }
  }

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      switch (e.key) {
        case 'Escape':
          onClose()
          break
        case 'ArrowLeft':
          if (hasPrev) onNavigate('prev')
          break
        case 'ArrowRight':
          if (hasNext) onNavigate('next')
          break
        case '1':
        case '2':
        case '3':
          const formatIndex = parseInt(e.key) - 1
          const availableFormats = [file?.file_type, ...siblingFiles.map(f => f.file_type)].filter(Boolean)
          if (availableFormats[formatIndex]) {
            switchFormat(availableFormats[formatIndex])
          }
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, hasPrev, hasNext, onClose, onNavigate, file, siblingFiles])

  // Update current file when file prop changes
  useEffect(() => {
    setCurrentFile(file)
  }, [file])

  // Fetch sibling files when file changes
  useEffect(() => {
    if (currentFile) {
      fetchSiblingFiles(currentFile)
      setSelectedFormat(currentFile.file_type)
    }
  }, [currentFile?.sha256])

  // Reset state when drawer closes
  useEffect(() => {
    if (!isOpen) {
      setShowMeta(false)
      setReportIssue(false)
      setIssueText('')
      setCopied(null)
    }
  }, [isOpen])

  if (!isOpen) return null

  const formatMap: Record<string, string> = {
    'rvt': 'Revit',
    'skp': 'SketchUp',
    'dwg': 'AutoCAD',
    'dxf': 'AutoCAD'
  }

  const availableFormats = currentFile ? [currentFile.file_type, ...siblingFiles.map(f => f.file_type)].filter(Boolean) : []
  const hasMultipleFormats = availableFormats.length > 1

  // Handle file updates
  const handleFileUpdate = async (field: string, value: string) => {
    if (!currentFile) return

    try {
      const response = await fetch('/api/files/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          sha256: currentFile.sha256, 
          updates: { [field]: value } 
        })
      })

      if (!response.ok) {
        throw new Error('Failed to update file')
      }

      const { data } = await response.json()
      setCurrentFile(data)
      
      // Update parent if callback exists
      if (onSwitchFormat) {
        onSwitchFormat(data)
      }
    } catch (error) {
      console.error('Update failed:', error)
      throw error
    }
  }

  const handleArchive = () => {
    // Close drawer after archiving
    onClose()
  }

  const handleThumbnailUpdate = (url: string) => {
    if (currentFile) {
      setCurrentFile({ ...currentFile, thumbnail_url: url })
    }
  }

  return (
    <TooltipProvider>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div
        ref={drawerRef}
        className={`fixed right-0 top-0 h-full w-[480px] bg-background border-l shadow-xl z-50 transform motion-slow radius-drawer ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between card-padding border-b">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigate('prev')}
              disabled={!hasPrev}
              className="focus-ring"
              aria-label="Previous file"
              title="Previous file (←)"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigate('next')}
              disabled={!hasNext}
              className="focus-ring"
              aria-label="Next file"
              title="Next file (→)"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="focus-ring"
            aria-label="Close drawer"
            title="Close drawer (Esc)"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

                 {/* Content */}
         <div className="h-full overflow-y-auto">
           {isLoading ? (
             <FileDrawerSkeleton />
           ) : currentFile ? (
            <>
                             {/* Hero Thumbnail */}
               <div className="relative h-64 bg-muted">
                 {currentFile.thumbnail_url && !imageError.has(currentFile.sha256) ? (
                   <Image
                     src={currentFile.thumbnail_url}
                     alt={currentFile.name || `3D Model - ${currentFile.file_type}`}
                     fill
                     className="object-cover"
                     onError={() => onImageError(currentFile.sha256)}
                     unoptimized
                     loading="lazy"
                     style={{ contentVisibility: 'auto' }}
                   />
                 ) : (
                   <div className="flex items-center justify-center h-full text-muted-foreground">
                     <div className="text-center">
                       <div className="text-4xl mb-4">📁</div>
                       <span className="text-lg">{currentFile.file_type?.toUpperCase()}</span>
                     </div>
                   </div>
                 )}
               </div>

              <div className="card-padding space-y-6">
                                 {/* Title */}
                 <div>
                   <h1 className="text-xl font-bold mb-1">
                     <InlineEdit
                       value={currentFile.name || `File ${currentFile.sha256?.slice(0, 8)}`}
                       field="name"
                       sha256={currentFile.sha256}
                       onUpdate={handleFileUpdate}
                       isAdmin={isAdmin}
                       className="text-xl font-bold"
                     />
                   </h1>
                   <p className="text-muted-foreground">
                     <InlineEdit
                       value={currentFile.brand || 'Unknown'}
                       field="brand"
                       sha256={currentFile.sha256}
                       onUpdate={handleFileUpdate}
                       isAdmin={isAdmin}
                       className="text-muted-foreground"
                     />
                     {' · '}
                     <InlineEdit
                       value={currentFile.furniture_type || 'Unknown'}
                       field="furniture_type"
                       sha256={currentFile.sha256}
                       onUpdate={handleFileUpdate}
                       isAdmin={isAdmin}
                       className="text-muted-foreground"
                     />
                   </p>
                 </div>

                                 {/* Essentials Pills */}
                 <div className="flex flex-wrap gap-2">
                   <Badge variant="outline">
                     <InlineEdit
                       value={formatMap[currentFile.file_type] || currentFile.file_type?.toUpperCase()}
                       field="file_type"
                       sha256={currentFile.sha256}
                       onUpdate={handleFileUpdate}
                       isAdmin={isAdmin}
                       className=""
                     />
                   </Badge>
                   <Badge variant="outline">
                     {currentFile.size_bytes ? `${(currentFile.size_bytes / (1024 * 1024)).toFixed(1)} MB` : 'Unknown'}
                   </Badge>
                   <div className="flex items-center gap-1">
                     <div className={`w-2 h-2 rounded-full ${
                       currentFile.status === 'active' ? 'bg-green-500' :
                       currentFile.status === 'pending' ? 'bg-yellow-500' :
                       'bg-red-500'
                     }`} />
                     <span className="text-xs text-muted-foreground">{currentFile.status}</span>
                   </div>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center gap-1 cursor-help">
                        <div className={`w-2 h-2 rounded-full ${
                          linkHealthStatus === 'ok' ? 'bg-green-500' :
                          linkHealthStatus === 'broken' ? 'bg-red-500' :
                          linkHealthStatus === 'checking' ? 'bg-yellow-500 animate-pulse' :
                          'bg-gray-400'
                        }`} />
                        <span className="text-xs text-muted-foreground">
                          {linkHealthStatus === 'ok' ? 'Link OK' :
                           linkHealthStatus === 'broken' ? 'Link Broken' :
                           linkHealthStatus === 'checking' ? 'Checking...' :
                           'Unknown'}
                        </span>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      {linkHealthStatus === 'ok' ? 'Link is accessible and working' :
                       linkHealthStatus === 'broken' ? 'Link is broken or inaccessible' :
                       linkHealthStatus === 'checking' ? 'Checking link accessibility...' :
                       'Link status unknown'}
                    </TooltipContent>
                  </Tooltip>
                </div>

                                 {/* Primary Actions */}
                 <div className="flex gap-2">
                   <Button
                     onClick={() => window.open(currentFile.product_url || currentFile.source_url, '_blank')}
                     className="flex-1 focus-ring"
                     aria-label={`Open product page for ${currentFile.name || 'file'}`}
                     disabled={!currentFile.product_url && !currentFile.source_url}
                   >
                     <ExternalLink className="h-4 w-4 mr-2" />
                     Open Product Page
                   </Button>
                   <Button
                     variant="outline"
                     onClick={() => copyToClipboard(currentFile.product_url || currentFile.source_url, 'url')}
                     className="focus-ring"
                     aria-label={`Copy URL for ${currentFile.name || 'file'}`}
                     disabled={!currentFile.product_url && !currentFile.source_url}
                   >
                     <Copy className="h-4 w-4 mr-2" />
                     {copied === 'url' && <CheckCircle className="h-4 w-4 mr-1 text-green-500" />}
                     Copy URL
                   </Button>
                   <Button
                     variant="outline"
                     onClick={() => window.open(currentFile.source_url, '_blank')}
                     className="focus-ring"
                     aria-label={`Download ${currentFile.name || 'file'}`}
                   >
                     <Download className="h-4 w-4 mr-2" />
                     Download
                   </Button>
                 </div>

                 {/* Admin Actions */}
                 <AdminActions
                   sha256={currentFile.sha256}
                   isAdmin={isAdmin}
                   onArchive={handleArchive}
                   onThumbnailUpdate={handleThumbnailUpdate}
                 />

                {/* Format Switcher */}
                {hasMultipleFormats && (
                  <div>
                    <h3 className="text-sm font-medium mb-2">Available Formats</h3>
                    <div className="flex gap-1">
                      {availableFormats.map((format) => (
                        <Button
                          key={format}
                          variant={selectedFormat === format ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => switchFormat(format)}
                          className="flex-1 focus-ring"
                          aria-label={`Switch to ${formatMap[format] || format?.toUpperCase()} format`}
                          aria-pressed={selectedFormat === format}
                        >
                          {formatMap[format] || format?.toUpperCase()}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                                 {/* Meta Section */}
                 <div>
                   <Button
                     variant="ghost"
                     size="sm"
                     onClick={() => setShowMeta(!showMeta)}
                     className="w-full justify-start text-muted-foreground focus-ring"
                     aria-expanded={showMeta}
                     aria-controls="meta-content"
                   >
                     <AlertCircle className="h-4 w-4 mr-2" />
                     Meta {showMeta ? '(Collapsed)' : '(Expanded)'}
                   </Button>
                   
                   {showMeta && (
                     <div id="meta-content" className="mt-3 space-y-3 p-3 bg-muted rounded-lg">
                       <div className="flex items-center justify-between">
                         <span className="text-sm text-muted-foreground">SHA256:</span>
                         <div className="flex items-center gap-2">
                           <code className="text-xs font-mono">
                             {currentFile.sha256?.slice(0, 16)}...
                           </code>
                           <Button
                             variant="ghost"
                             size="sm"
                             onClick={() => copyToClipboard(currentFile.sha256, 'sha256')}
                             className="focus-ring"
                             aria-label="Copy SHA256 hash"
                           >
                             <Copy className="h-3 w-3" />
                             {copied === 'sha256' && <CheckCircle className="h-3 w-3 ml-1 text-green-500" />}
                           </Button>
                         </div>
                       </div>
                       
                       <div className="flex justify-between text-sm">
                         <span className="text-muted-foreground">Created:</span>
                         <span>{new Date(currentFile.created_at).toLocaleDateString()}</span>
                       </div>
                       
                       {currentFile.updated_at && (
                         <div className="flex justify-between text-sm">
                           <span className="text-muted-foreground">Updated:</span>
                           <span>{new Date(currentFile.updated_at).toLocaleDateString()}</span>
                         </div>
                       )}
                       
                       {currentFile.tags && currentFile.tags.length > 0 && (
                         <div>
                           <span className="text-sm text-muted-foreground">Tags:</span>
                           <div className="flex flex-wrap gap-1 mt-1">
                             {currentFile.tags.map((tag, index) => (
                               <Badge key={index} variant="secondary" className="text-xs">
                                 {tag}
                               </Badge>
                             ))}
                           </div>
                         </div>
                       )}
                     </div>
                   )}
                 </div>

                 {/* Issue Triage Panel (Admin Only) */}
                 <IssueTriagePanel isAdmin={isAdmin} />

                {/* Report Issue */}
                <div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setReportIssue(!reportIssue)}
                    className="w-full justify-start text-muted-foreground focus-ring"
                    aria-expanded={reportIssue}
                    aria-controls="report-issue-content"
                  >
                    <AlertCircle className="h-4 w-4 mr-2" />
                    Report Issue
                  </Button>
                  
                                     {reportIssue && (
                     <div id="report-issue-content" className="mt-3 space-y-3 p-3 bg-muted rounded-lg">
                       <label htmlFor="issue-description" className="sr-only">Issue description</label>
                       <Input
                         id="issue-description"
                         placeholder="Describe the issue..."
                         value={issueText}
                         onChange={(e) => setIssueText(e.target.value)}
                         className="text-sm focus-ring"
                       />
                       <div className="flex gap-2">
                         <Button
                           size="sm"
                           onClick={async () => {
                             if (!currentFile) return
                             
                             try {
                               const response = await fetch('/api/issues', {
                                 method: 'POST',
                                 headers: { 'Content-Type': 'application/json' },
                                 body: JSON.stringify({
                                   sha256: currentFile.sha256,
                                   description: issueText
                                 })
                               })
                               
                               if (!response.ok) {
                                 throw new Error('Failed to submit issue')
                               }
                               
                               setIssueText('')
                               setReportIssue(false)
                               addToast('Issue reported successfully', 'success')
                             } catch (error) {
                               console.error('Failed to submit issue:', error)
                               addToast('Failed to submit issue', 'error')
                             }
                           }}
                           disabled={!issueText.trim()}
                           className="focus-ring"
                         >
                           Submit
                         </Button>
                         <Button
                           variant="outline"
                           size="sm"
                           onClick={() => {
                             setIssueText('')
                             setReportIssue(false)
                           }}
                           className="focus-ring"
                         >
                           Cancel
                         </Button>
                       </div>
                     </div>
                   )}
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </TooltipProvider>
  )
}
