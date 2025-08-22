import { supabase } from '@/lib/supabase'
import { isDatabaseConfigured } from '@/lib/utils'
import Image from 'next/image'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export default async function CardsPage() {
  // Check if database is configured
  if (!isDatabaseConfigured()) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>Product Cards</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-amber-600 bg-amber-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Configuration Required</h3>
              <p className="text-sm">
                Supabase environment variables are not configured. Please set the following in your Vercel environment:
              </p>
              <ul className="text-sm mt-2 space-y-1">
                <li>• <code className="bg-gray-100 px-1 rounded">NEXT_PUBLIC_SUPABASE_URL</code></li>
                <li>• <code className="bg-gray-100 px-1 rounded">NEXT_PUBLIC_SUPABASE_ANON_KEY</code></li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Fetch products
  let products = null
  let error = null

  try {
    const result = await supabase
      .from('products')
      .select('*')
      .order('name')
    
    products = result.data
    error = result.error
  } catch (err) {
    error = err as any
  }

  // Fetch images for all products
  let allImages = null
  try {
    const imagesResult = await supabase
      .from('images')
      .select('product_uid, image_url, score, is_primary')
      .eq('is_primary', true)
    allImages = imagesResult.data
  } catch (err) {
    console.error('Error fetching images:', err)
    allImages = []
  }

  // Fetch file counts for all products
  let allFiles = null
  try {
    const filesResult = await supabase
      .from('files')
      .select('product_uid')
    allFiles = filesResult.data
  } catch (err) {
    console.error('Error fetching files:', err)
    allFiles = []
  }

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
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>Product Cards</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-red-600">Error loading data: {error.message}</div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Product Cards</CardTitle>
              <CardDescription>Products with images and file information</CardDescription>
            </div>
            <Badge variant="secondary">
              {products?.length || 0} products
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {products && products.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {products.map((product: any) => (
                              <Card key={product.uid} className="overflow-hidden hover:shadow-lg transition-shadow">
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

                  <CardContent className="p-4">
                    <h3 className="text-lg font-semibold mb-1">
                      {product.name}
                    </h3>
                    <p className="text-sm text-muted-foreground mb-2">
                      {product.brand}
                    </p>
                    
                    {/* File Count Badge */}
                    <div className="flex items-center justify-between">
                      <Badge variant="outline">
                        {fileCountMap[product.uid] || 0} files
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        Score: {imageMap[product.uid]?.score?.toFixed(1) || 'N/A'}
                      </span>
                    </div>
                  </CardContent>
                </Card>
            ))}
          </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-muted-foreground">No products found</div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
