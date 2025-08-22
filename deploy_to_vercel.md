# 🚀 Vercel Deployment Guide

## Quick Deploy Steps:

### 1. Visit Vercel
- Go to: https://vercel.com
- Sign in with GitHub

### 2. Import Repository
- Click "New Project"
- Select: `iiko38/3d-model-extraction-webapp`
- Click "Import"

### 3. Configure Settings
- **Framework**: Other
- **Root Directory**: `./`
- **Build Command**: (leave empty)
- **Output Directory**: (leave empty)
- **Install Command**: `pip install -r requirements_cloud.txt`

### 4. Environment Variables
Add these in the Environment Variables section:

```
SUPABASE_URL=https://jcmnuxlusnfhusbulhag.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpjbW51eGx1c25maHVzYnVsaGFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU4NjY0NDQsImV4cCI6MjA3MTQ0MjQ0NH0.OktEF3rXOxvJcy5PZj52xGezQYKvUG-S9R5Vfb-HNwI
USE_CLOUD_STORAGE=true
CLOUD_STORAGE_BUCKET=3d-model-images
JWT_SECRET_KEY=your-secret-key-here
```

### 5. Deploy
- Click "Deploy"
- Wait for build completion

### 6. Test Your App
- Visit your Vercel URL
- Test all functionality:
  - Product browsing
  - File downloads
  - Search and filtering
  - Stats page

## Expected URL Format:
`https://your-project-name.vercel.app`

## Troubleshooting:
- If build fails, check the build logs
- Ensure all environment variables are set
- Verify Supabase connection is working

## Success Indicators:
- ✅ Build completes successfully
- ✅ App loads without errors
- ✅ Can browse products
- ✅ Can download files
- ✅ Search and filters work
