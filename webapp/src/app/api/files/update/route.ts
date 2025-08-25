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

    const { sha256, updates } = await request.json()

    if (!sha256) {
      return NextResponse.json({ error: 'SHA256 is required' }, { status: 400 })
    }

    if (!updates || typeof updates !== 'object') {
      return NextResponse.json({ error: 'Updates object is required' }, { status: 400 })
    }

    // Validate allowed fields
    const allowedFields = ['name', 'brand', 'file_type', 'furniture_type', 'tags', 'status', 'thumbnail_url']
    const validUpdates: any = {}
    
    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        validUpdates[key] = value
      }
    }

    if (Object.keys(validUpdates).length === 0) {
      return NextResponse.json({ error: 'No valid fields to update' }, { status: 400 })
    }

    // Add updated_at timestamp
    validUpdates.updated_at = new Date().toISOString()

    // Update the file
    const { data, error } = await supabase
      .from('files')
      .update(validUpdates)
      .eq('sha256', sha256)
      .select()
      .single()

    if (error) {
      console.error('Database update error:', error)
      return NextResponse.json({ error: 'Failed to update file' }, { status: 500 })
    }

    return NextResponse.json({ 
      success: true, 
      data,
      message: 'File updated successfully' 
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
