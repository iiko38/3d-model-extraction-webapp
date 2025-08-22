import { supabase } from '@/lib/supabase'
import { formatFileSize, isDatabaseConfigured } from '@/lib/utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'

export default async function HomePage() {
  // Check if database is configured
  if (!isDatabaseConfigured()) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>3D Model Library</CardTitle>
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

  // Fetch data from Supabase
  let files = null
  let error = null

  try {
    const result = await supabase
      .from('files')
      .select('*')
      .limit(50)
      .order('created_at', { ascending: false })
    
    files = result.data
    error = result.error
  } catch (err) {
    error = err as any
  }

  if (error) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>3D Model Library</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-red-600 bg-red-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Database Connection Error</h3>
              <p className="text-sm">{error.message}</p>
            </div>
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
              <CardTitle>3D Model Library</CardTitle>
              <CardDescription>Database-driven file management</CardDescription>
            </div>
            <Badge variant="secondary">
              {files?.length || 0} files loaded
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Brand</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {files?.map((file) => (
                  <TableRow key={file.sha256}>
                    <TableCell className="font-medium">{file.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{file.file_type}</Badge>
                    </TableCell>
                    <TableCell>{formatFileSize(file.size_bytes)}</TableCell>
                    <TableCell>{file.brand}</TableCell>
                    <TableCell>
                      <Badge variant={
                        file.status === 'active' ? 'default' :
                        file.status === 'pending' ? 'secondary' :
                        'destructive'
                      }>
                        {file.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{new Date(file.created_at).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <div className="mt-6 space-y-4">
            <div className="flex space-x-2">
              <Button variant="default">Add File</Button>
              <Button variant="outline">Export</Button>
              <Button variant="secondary">Settings</Button>
            </div>
            
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-semibold text-blue-900 mb-2">Quick Actions</h3>
              <div className="flex space-x-2">
                <Badge variant="outline" className="cursor-pointer hover:bg-blue-100">View Cards</Badge>
                <Badge variant="outline" className="cursor-pointer hover:bg-blue-100">View Stats</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
