import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import { isAdmin } from '@/lib/auth'

export async function POST(request: NextRequest) {
  try {
    // Check admin status
    const adminCheck = await isAdmin()
    if (!adminCheck) {
      return NextResponse.json({ error: 'Unauthorized - Admin access required' }, { status: 403 })
    }

    const { sha256, thumbnailUrl } = await request.json()

    if (!sha256) {
      return NextResponse.json({ error: 'SHA256 is required' }, { status: 400 })
    }

    if (!thumbnailUrl) {
      return NextResponse.json({ error: 'Thumbnail URL is required' }, { status: 400 })
    }

    // Validate URL format
    try {
      new URL(thumbnailUrl)
    } catch {
      return NextResponse.json({ error: 'Invalid thumbnail URL format' }, { status: 400 })
    }

    // Update the file thumbnail URL
    const { data, error } = await supabase
      .from('files')
      .update({ 
        thumbnail_url: thumbnailUrl,
        updated_at: new Date().toISOString()
      })
      .eq('sha256', sha256)
      .select()
      .single()

    if (error) {
      console.error('Database update error:', error)
      return NextResponse.json({ error: 'Failed to update thumbnail' }, { status: 500 })
    }

    return NextResponse.json({ 
      success: true, 
      data,
      message: 'Thumbnail updated successfully' 
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
