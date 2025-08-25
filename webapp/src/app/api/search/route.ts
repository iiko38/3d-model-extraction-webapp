import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const q = searchParams.get('q')
  const page = parseInt(searchParams.get('page') || '1')
  const limit = parseInt(searchParams.get('limit') || '20')
  const offset = (page - 1) * limit

  if (!q || q.length < 3) {
    return NextResponse.json({ error: 'Query must be at least 3 characters' }, { status: 400 })
  }

  try {
    // Use the new FTS RPC function for proper ranked search
    const { data, error } = await supabase.rpc('search_files', {
      query: q,
      page_num: page,
      page_size: limit
    })
    
    if (error) throw error
    
    if (!data || data.length === 0) {
      return NextResponse.json({
        results: [],
        pagination: {
          page,
          limit,
          totalCount: 0,
          totalPages: 0,
          hasNext: false,
          hasPrev: false
        }
      })
    }
    
    // Extract total count from the first row
    const totalCount = data[0]?.total_count || 0
    const totalPages = Math.ceil(totalCount / limit)
    
    // Remove total_count from results and map to expected format
    const results = data.map((row: any) => {
      const { total_count, ...file } = row
      return {
        ...file,
        _score: row.rank || 0
      }
    })
    
    return NextResponse.json({
      results,
      pagination: {
        page,
        limit,
        totalCount,
        totalPages,
        hasNext: page < totalPages,
        hasPrev: page > 1
      }
    })
  } catch (error) {
    console.error('Search error:', error)
    return NextResponse.json({ error: 'Search failed' }, { status: 500 })
  }
}
