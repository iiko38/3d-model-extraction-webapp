import { supabase } from '@/lib/supabase'
import { formatFileSize } from '@/lib/utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default async function StatsPage() {
  // Fetch basic counts
  const [
    { count: totalProducts },
    { count: totalFiles },
    { count: totalImages }
  ] = await Promise.all([
    supabase.from('products').select('*', { count: 'exact', head: true }),
    supabase.from('files').select('*', { count: 'exact', head: true }),
    supabase.from('images').select('*', { count: 'exact', head: true })
  ])

  // Fetch file types breakdown
  const { data: allFiles } = await supabase.from('files').select('file_type')
  const fileTypes = allFiles?.reduce((acc: any, file: any) => {
    acc[file.file_type] = (acc[file.file_type] || 0) + 1
    return acc
  }, {}) || {}

  // Fetch brands breakdown
  const { data: allProducts } = await supabase.from('products').select('brand')
  const brands = allProducts?.reduce((acc: any, product: any) => {
    acc[product.brand] = (acc[product.brand] || 0) + 1
    return acc
  }, {}) || {}

  // Fetch top products by file count
  const { data: allFilesForCount } = await supabase.from('files').select('product_uid')
  const productCounts = allFilesForCount?.reduce((acc: any, file: any) => {
    acc[file.product_uid] = (acc[file.product_uid] || 0) + 1
    return acc
  }, {}) || {}
  const topProducts = Object.entries(productCounts)
    .map(([product_uid, count]) => ({ product_uid, count }))
    .sort((a: any, b: any) => b.count - a.count)
    .slice(0, 10)

  // Fetch heaviest files
  const { data: heaviestFiles } = await supabase
    .from('files')
    .select('product_uid, size_bytes, file_type')
    .order('size_bytes', { ascending: false })
    .limit(10)

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle>Database Statistics</CardTitle>
          <CardDescription>Overview of your 3D model library</CardDescription>
        </CardHeader>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">P</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Total Products</p>
                <p className="text-2xl font-bold">{totalProducts || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">F</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Total Files</p>
                <p className="text-2xl font-bold">{totalFiles || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">I</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Total Images</p>
                <p className="text-2xl font-bold">{totalImages || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

                   {/* File Types Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>File Types</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(fileTypes).map(([fileType, count]: [string, any]) => (
              <div key={fileType} className="flex justify-between items-center">
                <span className="text-sm font-medium">{fileType}</span>
                <Badge variant="outline">{count} files</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Brands Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Brands</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(brands).map(([brand, count]: [string, any]) => (
              <div key={brand} className="flex justify-between items-center">
                <span className="text-sm font-medium">{brand}</span>
                <Badge variant="outline">{count} products</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Top Products by File Count */}
      <Card>
        <CardHeader>
          <CardTitle>Top Products by File Count</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {topProducts?.map((product: any, index: number) => (
              <div key={product.product_uid} className="flex justify-between items-center">
                <span className="text-sm font-medium">
                  {index + 1}. {product.product_uid}
                </span>
                <Badge variant="outline">{product.count} files</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Heaviest Files */}
      <Card>
        <CardHeader>
          <CardTitle>Heaviest Files</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {heaviestFiles?.map((file: any, index: number) => (
              <div key={index} className="flex justify-between items-center">
                <div>
                  <span className="text-sm font-medium">
                    {index + 1}. {file.product_uid}
                  </span>
                  <span className="text-xs text-muted-foreground ml-2">({file.file_type})</span>
                </div>
                <Badge variant="outline">{formatFileSize(file.size_bytes)}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
