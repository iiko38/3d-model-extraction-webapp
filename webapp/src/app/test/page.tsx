import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export default function TestPage() {
  return (
    <div className="p-6">
      <Card>
        <CardHeader>
          <CardTitle>UI Test Page</CardTitle>
          <CardDescription>Testing if UI components are working</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-2">Badges</h3>
              <div className="space-x-2">
                <Badge variant="default">Default</Badge>
                <Badge variant="secondary">Secondary</Badge>
                <Badge variant="outline">Outline</Badge>
                <Badge variant="destructive">Destructive</Badge>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Buttons</h3>
              <div className="space-x-2">
                <Button variant="default">Default</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="destructive">Destructive</Button>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Sample Data</h3>
              <div className="bg-gray-50 p-4 rounded">
                <p>If you can see this styled content, the UI is working!</p>
                <p className="text-sm text-gray-600 mt-2">This page doesn't use Supabase, so it should always work.</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
