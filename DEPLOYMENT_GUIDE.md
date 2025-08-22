# 🚀 Cloud Deployment Guide: Local → Vercel + Supabase

## Overview

This guide walks you through migrating the 3D Model Extraction application from local SQLite to a cloud-native architecture using Vercel for hosting and Supabase for the database.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Local Scripts │    │   Supabase      │    │   Vercel        │
│   (Data Sync)   │───▶│   PostgreSQL    │◄───│   FastAPI App   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Local Files    │    │  Cloud Storage  │    │  Static Assets  │
│  (3D Models)    │    │  (Images)       │    │  (CSS/JS)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Phase 1: Supabase Setup

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note down your project URL and API keys

### 1.2 Install Dependencies

```bash
pip install -r requirements_cloud.txt
```

### 1.3 Set Environment Variables

Create a `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Cloud Storage
USE_CLOUD_STORAGE=true
CLOUD_STORAGE_BUCKET=3d-model-images

# Security
JWT_SECRET_KEY=your-secret-key
```

### 1.4 Run Database Migration

```bash
python supabase_migration.py
```

This will:
- Create the PostgreSQL schema
- Migrate all data from SQLite to Supabase
- Verify the migration

## Phase 2: Vercel Deployment

### 2.1 Install Vercel CLI

```bash
npm install -g vercel
```

### 2.2 Configure Vercel

1. Login to Vercel:
```bash
vercel login
```

2. Initialize project:
```bash
vercel init
```

3. Configure environment variables in Vercel dashboard:
   - Go to your project settings
   - Add all environment variables from `.env`

### 2.3 Deploy to Vercel

```bash
vercel --prod
```

## Phase 3: Local Sync Setup

### 3.1 Configure Local Sync

The local sync manager keeps Supabase updated with new data from your scrapes:

```bash
# Run full sync (first time)
python local_sync_manager.py

# Run incremental sync (regular updates)
python -c "
import asyncio
from local_sync_manager import LocalSyncManager
sync_manager = LocalSyncManager()
asyncio.run(sync_manager.run_incremental_sync())
"
```

### 3.2 Automated Sync (Optional)

Create a scheduled task to run sync automatically:

```bash
# Windows Task Scheduler or cron job
# Run every 6 hours: 0 */6 * * * python local_sync_manager.py
```

## Phase 4: File Storage Strategy

### 4.1 3D Files (Local Only)

3D model files remain local for performance and cost reasons:

```
library/
├── herman_miller/
│   ├── aeron-chair/
│   │   ├── aeron-chair.skp
│   │   └── aeron-chair.rfa
│   └── ...
└── ...
```

### 4.2 Images (Hybrid Storage)

Images are stored both locally and in Supabase Storage:

- **Local**: For fast access during development
- **Cloud**: For production web app access

## Phase 5: Testing & Validation

### 5.1 Test Local Sync

```bash
# Test sync without uploading images
python -c "
import asyncio
from local_sync_manager import LocalSyncManager
sync_manager = LocalSyncManager()
asyncio.run(sync_manager.run_incremental_sync())
"
```

### 5.2 Test Cloud Application

1. Visit your Vercel deployment URL
2. Test all functionality:
   - Product browsing
   - File downloads
   - Image display
   - Search and filtering

### 5.3 Health Check

```bash
curl https://your-vercel-app.vercel.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "version": "2.0.0",
  "environment": "cloud"
}
```

## Phase 6: Production Optimization

### 6.1 Performance Monitoring

Monitor these metrics:
- API response times
- Database query performance
- File download speeds
- Sync operation success rates

### 6.2 Cost Optimization

- Monitor Supabase usage
- Optimize image storage
- Use CDN for static assets

### 6.3 Security

- Rotate API keys regularly
- Monitor access logs
- Implement rate limiting if needed

## Troubleshooting

### Common Issues

1. **Migration Fails**
   - Check Supabase credentials
   - Verify local database exists
   - Check network connectivity

2. **Sync Errors**
   - Verify environment variables
   - Check local database permissions
   - Monitor Supabase quotas

3. **Deployment Issues**
   - Check Vercel build logs
   - Verify environment variables
   - Test locally first

### Debug Commands

```bash
# Check Supabase connection
python -c "
from supabase import create_client
client = create_client('YOUR_URL', 'YOUR_KEY')
print(client.table('products').select('*').limit(1).execute())
"

# Check local database
python -c "
import sqlite3
conn = sqlite3.connect('library/index.sqlite')
print(conn.execute('SELECT COUNT(*) FROM products').fetchone())
"
```

## Maintenance

### Regular Tasks

1. **Daily**: Check sync logs
2. **Weekly**: Monitor performance metrics
3. **Monthly**: Review costs and optimize
4. **Quarterly**: Update dependencies

### Backup Strategy

- Supabase provides automatic backups
- Keep local SQLite as backup
- Export data regularly using the export scripts

## Support

For issues:
1. Check the logs in Vercel dashboard
2. Monitor Supabase dashboard
3. Review sync manager logs
4. Test locally first

## Success Metrics

- **Uptime**: > 99.9%
- **Sync Latency**: < 5 minutes
- **API Response**: < 200ms
- **Cost**: Within budget
- **User Experience**: Seamless

---

**🎉 Congratulations! Your application is now cloud-native and ready for production!**
