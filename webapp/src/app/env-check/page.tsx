export default function EnvCheckPage() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  return (
    <div className="p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Environment Variables Check</h1>
        
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-lg border">
            <h2 className="font-semibold mb-2">Supabase URL</h2>
            <div className="text-sm">
              {supabaseUrl ? (
                <div className="text-green-600">
                  ✅ Set: {supabaseUrl.substring(0, 30)}...
                </div>
              ) : (
                <div className="text-red-600">❌ Missing</div>
              )}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border">
            <h2 className="font-semibold mb-2">Supabase Anon Key</h2>
            <div className="text-sm">
              {supabaseKey ? (
                <div className="text-green-600">
                  ✅ Set: {supabaseKey.substring(0, 20)}...
                </div>
              ) : (
                <div className="text-red-600">❌ Missing</div>
              )}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border">
            <h2 className="font-semibold mb-2">Environment</h2>
            <div className="text-sm">
              <div>Node Environment: {process.env.NODE_ENV}</div>
              <div>Vercel Environment: {process.env.VERCEL_ENV || 'Not set'}</div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border">
            <h2 className="font-semibold mb-2">Instructions</h2>
            <div className="text-sm space-y-2">
              <p>If any variables are missing, add them to your Vercel environment:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Go to your Vercel dashboard</li>
                <li>Select your project</li>
                <li>Go to Settings → Environment Variables</li>
                <li>Add the missing variables</li>
                <li>Redeploy your project</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
