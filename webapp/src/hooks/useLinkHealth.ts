import { useState, useEffect, useRef } from 'react'

type LinkHealthStatus = 'unknown' | 'checking' | 'ok' | 'broken'

interface LinkHealthCache {
  [url: string]: {
    status: LinkHealthStatus
    timestamp: number
  }
}

// In-memory cache for the session
const linkHealthCache: LinkHealthCache = {}

export function useLinkHealth(url: string | null) {
  const [status, setStatus] = useState<LinkHealthStatus>('unknown')
  const debounceRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    if (!url) {
      setStatus('unknown')
      return
    }

    // Check cache first
    const cached = linkHealthCache[url]
    if (cached) {
      setStatus(cached.status)
      return
    }

    // Debounce the check
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    debounceRef.current = setTimeout(async () => {
      // Set checking status
      setStatus('checking')
      linkHealthCache[url] = { status: 'checking', timestamp: Date.now() }

      try {
        const response = await fetch(`/api/check?u=${encodeURIComponent(url)}`)
        const data = await response.json()
        
        const newStatus: LinkHealthStatus = data.ok ? 'ok' : 'broken'
        setStatus(newStatus)
        linkHealthCache[url] = { status: newStatus, timestamp: Date.now() }
      } catch (error) {
        console.error('Link health check failed:', error)
        const newStatus: LinkHealthStatus = 'broken'
        setStatus(newStatus)
        linkHealthCache[url] = { status: newStatus, timestamp: Date.now() }
      }
    }, 300) // 300ms debounce

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [url])

  return status
}
