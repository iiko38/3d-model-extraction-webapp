-- Test script for the migration
-- Run this after applying the migration to verify everything works

-- 1. Test the new fields exist
SELECT 
  name, 
  product_slug, 
  link_health,
  search IS NOT NULL as has_search_vector
FROM files 
LIMIT 5;

-- 2. Test the basic FTS function
SELECT 
  name, 
  brand, 
  furniture_type,
  rank
FROM fts_files('chair')
LIMIT 10;

-- 3. Test the advanced search function
SELECT 
  name, 
  brand, 
  furniture_type,
  file_type,
  rank,
  total_count
FROM search_files(
  query := 'chair',
  file_type_filter := 'rvt',
  page_num := 1,
  page_size := 5
);

-- 4. Test search with filters
SELECT 
  name, 
  brand, 
  furniture_type,
  file_type,
  status,
  rank
FROM search_files(
  query := 'table',
  brand_filter := 'herman miller',
  page_num := 1,
  page_size := 10
);

-- 5. Test sorting
SELECT 
  name, 
  created_at,
  rank
FROM search_files(
  query := 'chair',
  sort_by := 'created_at',
  sort_order := 'desc',
  page_num := 1,
  page_size := 5
);

-- 6. Test pagination
SELECT 
  name,
  rank
FROM search_files(
  query := 'chair',
  page_num := 2,
  page_size := 3
);

-- 7. Check indexes were created
SELECT 
  indexname, 
  indexdef 
FROM pg_indexes 
WHERE tablename = 'files' 
ORDER BY indexname;

-- 8. Check functions were created
SELECT 
  proname, 
  prosrc 
FROM pg_proc 
WHERE proname IN ('fts_files', 'search_files', 'update_files_search_vector')
ORDER BY proname;

-- 9. Check trigger was created
SELECT 
  trigger_name, 
  event_manipulation, 
  action_statement
FROM information_schema.triggers 
WHERE event_object_table = 'files';
