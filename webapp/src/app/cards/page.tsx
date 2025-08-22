import { supabase } from '@/lib/supabase'
import { formatFileSize } from '@/lib/utils'
import Image from 'next/image'

export default async function CardsPage() {
  // Fetch products
  const { data: products, error } = await supabase
    .from('products')
    .select('*')
    .order('name')

  // Fetch images for all products
  const { data: allImages } = await supabase
    .from('images')
    .select('product_uid, image_url, score, is_primary')
    .eq('is_primary', true)

  // Fetch file counts for all products
  const { data: allFiles } = await supabase
    .from('files')
    .select('product_uid')

  // Create lookup maps
  const imageMap = allImages?.reduce((acc: any, img: any) => {
    acc[img.product_uid] = img
    return acc
  }, {}) || {}

  const fileCountMap = allFiles?.reduce((acc: any, file: any) => {
    acc[file.product_uid] = (acc[file.product_uid] || 0) + 1
    return acc
  }, {}) || {}

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Product Cards</h1>
        <div className="text-red-600">Error loading data: {error.message}</div>
      </div>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Product Cards</h1>
            <p className="text-sm text-gray-600 mt-1">Products with images and file information</p>
          </div>
          <div className="text-sm text-gray-500">
            {products?.length || 0} products
          </div>
        </div>
      </div>

      {/* Product Cards Grid */}
      <div className="p-6">
        {products && products.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product: any) => (
              <div key={product.uid} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                                 {/* Product Image */}
                 <div className="relative h-48 bg-gray-100 rounded-t-lg overflow-hidden">
                   {imageMap[product.uid]?.image_url ? (
                     <Image
                       src={imageMap[product.uid].image_url}
                       alt={product.name}
                       fill
                       className="object-cover"
                     />
                   ) : (
                     <div className="flex items-center justify-center h-full text-gray-400">
                       <span>No Image</span>
                     </div>
                   )}
                 </div>

                 {/* Product Info */}
                 <div className="p-4">
                   <h3 className="text-lg font-semibold text-gray-900 mb-1">
                     {product.name}
                   </h3>
                   <p className="text-sm text-gray-600 mb-2">
                     {product.brand}
                   </p>
                   
                   {/* File Count Badge */}
                   <div className="flex items-center justify-between">
                     <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                       {fileCountMap[product.uid] || 0} files
                     </span>
                     <span className="text-xs text-gray-500">
                       Score: {imageMap[product.uid]?.score?.toFixed(1) || 'N/A'}
                     </span>
                   </div>
                 </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-gray-500">No products found</div>
          </div>
        )}
      </div>
    </div>
  )
}
