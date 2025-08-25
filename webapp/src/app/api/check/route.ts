import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const url = searchParams.get('u')

  if (!url) {
    return NextResponse.json({ error: 'URL parameter required' }, { status: 400 })
  }

  try {
    // Validate URL format
    const urlObj = new URL(url)
    
    // Perform HEAD request with 3-second timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 3000)

    const response = await fetch(url, {
      method: 'HEAD',
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; 3D-Model-Checker/1.0)'
      }
    })

    clearTimeout(timeoutId)

    // Consider 2xx and 3xx status codes as "OK"
    const ok = response.status >= 200 && response.status < 400

    return NextResponse.json({ ok })
  } catch (error) {
    // Handle various errors (timeout, network, invalid URL, etc.)
    console.error('Link check failed:', error)
    return NextResponse.json({ ok: false })
  }
}
