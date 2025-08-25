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

    const { sha256 } = await request.json()

    if (!sha256) {
      return NextResponse.json({ error: 'SHA256 is required' }, { status: 400 })
    }

    // Update the file status to archived
    const { data, error } = await supabase
      .from('files')
      .update({ 
        status: 'archived',
        updated_at: new Date().toISOString()
      })
      .eq('sha256', sha256)
      .select()
      .single()

    if (error) {
      console.error('Database update error:', error)
      return NextResponse.json({ error: 'Failed to archive file' }, { status: 500 })
    }

    return NextResponse.json({ 
      success: true, 
      data,
      message: 'File archived successfully' 
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
