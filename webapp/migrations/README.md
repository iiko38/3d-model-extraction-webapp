# Database Migrations

## Migration: 001_add_search_fields_and_fts.sql

This migration adds full-text search capabilities and new fields to the files table.

### ⚠️ **IMPORTANT: Development Only**

**DO NOT run this migration directly in production!** This migration should be:
1. Tested thoroughly in development
2. Reviewed by your team
3. Applied through your proper deployment process

### What This Migration Does

1. **Adds `product_slug`** - Generated column that creates URL-friendly slugs from file names
2. **Adds `link_health`** - Tracks the health status of source URLs ('unknown', 'ok', 'broken')
3. **Adds `search` TSVECTOR** - Full-text search vector with weighted fields:
   - Name (weight A - highest priority)
   - Brand (weight B)
   - Furniture Type (weight C)
   - Tags (weight D - lowest priority)
4. **Creates indexes** for optimal query performance
5. **Creates FTS functions** for ranked search results

### How to Apply (Development)

```bash
# Connect to your local Supabase database
psql "postgresql://postgres:[password]@localhost:54322/postgres"

# Run the migration
\i migrations/001_add_search_fields_and_fts.sql
```

### Testing the Migration

After running the migration, test the new functionality:

```sql
-- Test the FTS function
SELECT * FROM fts_files('chair');

-- Test the advanced search function
SELECT * FROM search_files(
  query := 'chair',
  file_type_filter := 'rvt',
  page_num := 1,
  page_size := 10
);

-- Verify the new fields exist
SELECT name, product_slug, link_health FROM files LIMIT 5;
```

### Performance Impact

- **Index creation** may take time on large tables
- **Search vector population** will update all existing records
- **Query performance** should improve significantly for search operations

### Rollback Plan

If you need to rollback, create a reverse migration:

```sql
-- Drop functions
DROP FUNCTION IF EXISTS fts_files(TEXT);
DROP FUNCTION IF EXISTS search_files(TEXT, TEXT, TEXT, TEXT, TEXT, BIGINT, BIGINT, TEXT, TEXT, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS update_files_search_vector();

-- Drop trigger
DROP TRIGGER IF EXISTS files_search_vector_update ON files;

-- Drop indexes
DROP INDEX IF EXISTS files_search_idx;
DROP INDEX IF EXISTS files_brand_idx;
DROP INDEX IF EXISTS files_file_type_idx;
DROP INDEX IF EXISTS files_furniture_type_idx;
DROP INDEX IF EXISTS files_status_idx;
DROP INDEX IF EXISTS files_created_at_idx;
DROP INDEX IF EXISTS files_product_slug_idx;
DROP INDEX IF EXISTS files_link_health_idx;

-- Drop columns
ALTER TABLE files DROP COLUMN IF EXISTS search;
ALTER TABLE files DROP COLUMN IF EXISTS link_health;
ALTER TABLE files DROP COLUMN IF EXISTS product_slug;
```

### Next Steps

After applying this migration:

1. Update your application code to use the new `search_files` RPC
2. Test search functionality with various queries
3. Monitor performance and adjust indexes if needed
4. Update your deployment process to include this migration
