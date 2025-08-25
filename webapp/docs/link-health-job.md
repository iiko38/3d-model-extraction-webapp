# Link Health Job

A server-side job that periodically checks the health of file source URLs and updates their status in the database.

## Overview

The link health job scans files with `link_health='unknown'` or files that haven't been checked in the last 7 days, performs HEAD requests to their `source_url`, and updates the database with the results.

## Features

- **Rate Limiting**: 500ms delay between requests to avoid being blocked
- **Timeout Handling**: 10-second timeout per request
- **Batch Processing**: Configurable limit for processing files
- **Dry Run Mode**: Test without making database changes
- **Error Logging**: Comprehensive error tracking and reporting
- **User-Agent**: Proper user agent to identify the checker

## API Endpoints

### POST `/api/jobs/link-health`

Main endpoint for running the job.

**Request Body:**
```json
{
  "limit": 10,        // Number of files to process (default: 10)
  "dryRun": false     // Test mode without database updates (default: false)
}
```

**Response:**
```json
{
  "message": "Link health check completed",
  "checked": 10,      // Number of files checked
  "updated": 8,       // Number of files updated in database
  "ok": 6,           // Number of healthy links
  "broken": 2,       // Number of broken links
  "errors": 0,       // Number of processing errors
  "results": [...]   // Detailed results (only in dry run mode)
}
```

### GET `/api/jobs/link-health`

Convenience endpoint for manual triggering.

**Query Parameters:**
- `limit`: Number of files to process (default: 5)
- `dryRun`: Test mode (default: false)

## Testing

### Manual Testing

```bash
# Test with curl
curl -X POST http://localhost:3000/api/jobs/link-health \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "dryRun": true}'

# Or use the test scripts
node scripts/test-link-health-job.js
# or
powershell scripts/test-link-health-job.ps1
```

### Browser Testing

Visit: `http://localhost:3000/api/jobs/link-health?limit=5&dryRun=true`

## Scheduling

### Development

For development, you can manually trigger the job or set up a simple cron job:

```bash
# Run every hour
0 * * * * curl -X POST http://localhost:3000/api/jobs/link-health -H "Content-Type: application/json" -d '{"limit": 50}'
```

### Production

For production, consider:

1. **Vercel Cron Jobs** (if using Vercel):
   ```typescript
   // vercel.json
   {
     "crons": [{
       "path": "/api/jobs/link-health",
       "schedule": "0 2 * * *"
     }]
   }
   ```

2. **Supabase Edge Functions** (if using Supabase):
   ```sql
   -- Create a scheduled function
   SELECT cron.schedule(
     'link-health-check',
     '0 2 * * *',
     'SELECT net.http_post(url:=''https://your-app.vercel.app/api/jobs/link-health'', headers:=''{"Content-Type": "application/json"}''::jsonb, body:=''{"limit": 100}''::jsonb);'
   );
   ```

3. **External Services**: GitHub Actions, AWS Lambda, etc.

## Configuration

### Environment Variables

- `NEXT_PUBLIC_APP_URL`: Base URL for the application (used in test scripts)

### Database Requirements

The job requires the `link_health` field to be added to the `files` table:

```sql
ALTER TABLE files 
ADD COLUMN link_health TEXT DEFAULT 'unknown' 
CHECK (link_health IN ('unknown', 'ok', 'broken'));
```

## Monitoring

### Logs

The job logs detailed information to the console:

```
[Link Health Job] Starting with limit: 10, dryRun: false
[Link Health Job] Found 10 files to check
[Link Health Job] Checking 1/10: abc123...
[Link Health Job] Checking 2/10: def456...
[Link Health Job] Updated 10 files
[Link Health Job] Summary: 8 OK, 2 broken, 0 errors
```

### Metrics

Track these metrics for monitoring:

- **Success Rate**: `ok / checked`
- **Error Rate**: `errors / checked`
- **Processing Time**: Time to complete the job
- **Database Updates**: Number of records updated

## Error Handling

The job handles various error scenarios:

- **Network Timeouts**: 10-second timeout per request
- **Invalid URLs**: Graceful handling of malformed URLs
- **Rate Limiting**: 500ms delay between requests
- **Database Errors**: Rollback on update failures
- **Partial Failures**: Continue processing even if some files fail

## Security Considerations

- **Rate Limiting**: Prevents overwhelming target servers
- **User-Agent**: Identifies the checker to avoid being blocked
- **Timeout**: Prevents hanging requests
- **Input Validation**: Validates URLs before processing

## Future Enhancements

1. **Retry Logic**: Retry failed requests with exponential backoff
2. **Priority Queue**: Prioritize files based on importance
3. **Webhook Notifications**: Notify on broken links
4. **Analytics Dashboard**: Visualize link health trends
5. **Bulk Operations**: Process larger batches efficiently
