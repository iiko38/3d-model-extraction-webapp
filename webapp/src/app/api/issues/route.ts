import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import { isAdmin } from '@/lib/auth'

export async function GET(request: NextRequest) {
  try {
    // Check admin status
    const adminCheck = await isAdmin()
    if (!adminCheck) {
      return NextResponse.json({ error: 'Unauthorized - Admin access required' }, { status: 403 })
    }

    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '10')

    // For now, we'll return a placeholder since file_issues table doesn't exist yet
    // This can be updated when the table is created
    const placeholderIssues = [
      {
        id: 1,
        sha256: 'placeholder-sha256-1',
        description: 'Sample issue report - thumbnail not loading',
        status: 'open',
        created_at: new Date().toISOString(),
        user_email: 'user@example.com'
      },
      {
        id: 2,
        sha256: 'placeholder-sha256-2',
        description: 'Sample issue report - broken download link',
        status: 'resolved',
        created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
        user_email: 'admin@example.com'
      }
    ]

    return NextResponse.json({ 
      issues: placeholderIssues.slice(0, limit),
      total: placeholderIssues.length
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    // Check admin status
    const adminCheck = await isAdmin()
    if (!adminCheck) {
      return NextResponse.json({ error: 'Unauthorized - Admin access required' }, { status: 403 })
    }

    const { sha256, description, status } = await request.json()

    if (!sha256) {
      return NextResponse.json({ error: 'SHA256 is required' }, { status: 400 })
    }

    if (!description) {
      return NextResponse.json({ error: 'Description is required' }, { status: 400 })
    }

    // For now, we'll just return success since file_issues table doesn't exist yet
    // This can be updated when the table is created
    const newIssue = {
      id: Date.now(),
      sha256,
      description,
      status: status || 'open',
      created_at: new Date().toISOString(),
      user_email: 'admin@example.com'
    }

    return NextResponse.json({ 
      success: true, 
      data: newIssue,
      message: 'Issue created successfully' 
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
