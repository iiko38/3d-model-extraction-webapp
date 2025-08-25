import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

interface LinkHealthResult {
  sha256: string
  source_url: string
  link_health: 'unknown' | 'ok' | 'broken'
  error?: string
}

export async function POST(request: NextRequest) {
  try {
    const { limit = 10, dryRun = false } = await request.json()
    
    console.log(`[Link Health Job] Starting with limit: ${limit}, dryRun: ${dryRun}`)
    
    // Get files that need checking
    const { data: filesToCheck, error: fetchError } = await supabase
      .from('files')
      .select('sha256, source_url, link_health, updated_at')
      .or('link_health.eq.unknown,updated_at.lt.now()-interval\'7 days\'')
      .limit(limit)
    
    if (fetchError) {
      console.error('[Link Health Job] Error fetching files:', fetchError)
      return NextResponse.json({ error: 'Failed to fetch files' }, { status: 500 })
    }
    
    if (!filesToCheck || filesToCheck.length === 0) {
      console.log('[Link Health Job] No files need checking')
      return NextResponse.json({ 
        message: 'No files need checking',
        checked: 0,
        updated: 0,
        errors: 0
      })
    }
    
    console.log(`[Link Health Job] Found ${filesToCheck.length} files to check`)
    
    const results: LinkHealthResult[] = []
    const updates: { sha256: string; link_health: string; updated_at: string }[] = []
    let errorCount = 0
    
    // Process files with rate limiting
    for (let i = 0; i < filesToCheck.length; i++) {
      const file = filesToCheck[i]
      
      try {
        console.log(`[Link Health Job] Checking ${i + 1}/${filesToCheck.length}: ${file.sha256}`)
        
        const healthResult = await checkLinkHealth(file.source_url)
        
        results.push({
          sha256: file.sha256,
          source_url: file.source_url,
          link_health: healthResult.ok ? 'ok' : 'broken',
          error: healthResult.error
        })
        
        if (!dryRun) {
          updates.push({
            sha256: file.sha256,
            link_health: healthResult.ok ? 'ok' : 'broken',
            updated_at: new Date().toISOString()
          })
        }
        
        // Rate limiting: wait 500ms between requests
        if (i < filesToCheck.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 500))
        }
        
      } catch (error) {
        console.error(`[Link Health Job] Error checking ${file.sha256}:`, error)
        errorCount++
        
        results.push({
          sha256: file.sha256,
          source_url: file.source_url,
          link_health: 'broken',
          error: error instanceof Error ? error.message : 'Unknown error'
        })
      }
    }
    
    // Update database if not dry run
    let updateCount = 0
    if (!dryRun && updates.length > 0) {
      try {
        const { error: updateError } = await supabase
          .from('files')
          .upsert(updates, { onConflict: 'sha256' })
        
        if (updateError) {
          console.error('[Link Health Job] Error updating files:', updateError)
          return NextResponse.json({ error: 'Failed to update files' }, { status: 500 })
        }
        
        updateCount = updates.length
        console.log(`[Link Health Job] Updated ${updateCount} files`)
        
      } catch (error) {
        console.error('[Link Health Job] Error in batch update:', error)
        return NextResponse.json({ error: 'Failed to update files' }, { status: 500 })
      }
    }
    
    // Log summary
    const okCount = results.filter(r => r.link_health === 'ok').length
    const brokenCount = results.filter(r => r.link_health === 'broken').length
    
    console.log(`[Link Health Job] Summary: ${okCount} OK, ${brokenCount} broken, ${errorCount} errors`)
    
    return NextResponse.json({
      message: 'Link health check completed',
      checked: filesToCheck.length,
      updated: updateCount,
      ok: okCount,
      broken: brokenCount,
      errors: errorCount,
      results: dryRun ? results : undefined // Only return results in dry run mode
    })
    
  } catch (error) {
    console.error('[Link Health Job] Unexpected error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

// Helper function to check link health
async function checkLinkHealth(url: string): Promise<{ ok: boolean; error?: string }> {
  if (!url) {
    return { ok: false, error: 'No URL provided' }
  }
  
  try {
    const urlObj = new URL(url)
    
    // Create abort controller for timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
    
    const response = await fetch(url, {
      method: 'HEAD',
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; 3D-Model-Link-Health-Checker/1.0)'
      }
    })
    
    clearTimeout(timeoutId)
    
    // Consider 2xx and 3xx status codes as "OK"
    const ok = response.status >= 200 && response.status < 400
    
    return { ok }
    
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return { ok: false, error: 'Request timeout' }
      }
      return { ok: false, error: error.message }
    }
    return { ok: false, error: 'Unknown error' }
  }
}

// GET endpoint for manual triggering and status
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const limit = parseInt(searchParams.get('limit') || '5')
  const dryRun = searchParams.get('dryRun') === 'true'
  
  console.log(`[Link Health Job] Manual trigger with limit: ${limit}, dryRun: ${dryRun}`)
  
  // Create a mock POST request body
  const body = JSON.stringify({ limit, dryRun })
  
  // Create a new request with the body
  const mockRequest = new NextRequest(request.url, {
    method: 'POST',
    headers: request.headers,
    body
  })
  
  return POST(mockRequest)
}
