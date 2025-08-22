import { supabase } from '@/lib/supabase'
import { formatFileSize } from '@/lib/utils'

export default async function StatsPage() {
  // Fetch various statistics
  const [
    { count: totalProducts },
    { count: totalFiles },
    { count: totalImages },
    { data: fileTypes },
    { data: brands },
    { data: topProducts },
    { data: heaviestFiles }
  ] = await Promise.all([
    supabase.from('products').select('*', { count: 'exact', head: true }),
    supabase.from('files').select('*', { count: 'exact', head: true }),
    supabase.from('images').select('*', { count: 'exact', head: true }),
    supabase.from('files').select('file_type').select('file_type, count').group('file_type').order('count', { ascending: false }),
    supabase.from('products').select('brand').select('brand, count').group('brand').order('count', { ascending: false }),
    supabase.from('files').select('product_uid, count').group('product_uid').order('count', { ascending: false }).limit(10),
    supabase.from('files').select('product_uid, size_bytes, file_type').order('size_bytes', { ascending: false }).limit(10)
  ])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Database Statistics</h1>
        <p className="text-sm text-gray-600">Overview of your 3D model library</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">P</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Products</p>
              <p className="text-2xl font-bold text-gray-900">{totalProducts || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">F</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Files</p>
              <p className="text-2xl font-bold text-gray-900">{totalFiles || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">I</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Images</p>
              <p className="text-2xl font-bold text-gray-900">{totalImages || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* File Types Breakdown */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">File Types</h2>
        <div className="space-y-2">
          {fileTypes?.map((type: any) => (
            <div key={type.file_type} className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">{type.file_type}</span>
              <span className="text-sm text-gray-500">{type.count} files</span>
            </div>
          ))}
        </div>
      </div>

      {/* Brands Breakdown */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Brands</h2>
        <div className="space-y-2">
          {brands?.map((brand: any) => (
            <div key={brand.brand} className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">{brand.brand}</span>
              <span className="text-sm text-gray-500">{brand.count} products</span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Products by File Count */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Products by File Count</h2>
        <div className="space-y-2">
          {topProducts?.map((product: any, index: number) => (
            <div key={product.product_uid} className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">
                {index + 1}. {product.product_uid}
              </span>
              <span className="text-sm text-gray-500">{product.count} files</span>
            </div>
          ))}
        </div>
      </div>

      {/* Heaviest Files */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Heaviest Files</h2>
        <div className="space-y-2">
          {heaviestFiles?.map((file: any, index: number) => (
            <div key={index} className="flex justify-between items-center">
              <div>
                <span className="text-sm font-medium text-gray-700">
                  {index + 1}. {file.product_uid}
                </span>
                <span className="text-xs text-gray-500 ml-2">({file.file_type})</span>
              </div>
              <span className="text-sm text-gray-500">{formatFileSize(file.size_bytes)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
