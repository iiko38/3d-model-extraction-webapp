-- Migration: Add search fields and FTS functionality to files table
-- Run this in development only, not in production

-- 1. Add product_slug field (generated column)
ALTER TABLE files 
ADD COLUMN product_slug TEXT GENERATED ALWAYS AS (
  regexp_replace(
    lower(coalesce(name, '')), 
    '[^a-z0-9]+', 
    '-', 
    'g'
  )
) STORED;

-- 2. Add link_health field with constraint
ALTER TABLE files 
ADD COLUMN link_health TEXT DEFAULT 'unknown' 
CHECK (link_health IN ('unknown', 'ok', 'broken'));

-- 3. Add search vector field
ALTER TABLE files 
ADD COLUMN search TSVECTOR;

-- 4. Create function to update search vector
CREATE OR REPLACE FUNCTION update_files_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search := 
    setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.brand, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.furniture_type, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'D');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5. Create trigger to automatically update search vector
CREATE TRIGGER files_search_vector_update
  BEFORE INSERT OR UPDATE ON files
  FOR EACH ROW
  EXECUTE FUNCTION update_files_search_vector();

-- 6. Create GIN index on search vector
CREATE INDEX files_search_idx ON files USING GIN (search);

-- 7. Create simple indexes for common queries
CREATE INDEX files_brand_idx ON files (brand);
CREATE INDEX files_file_type_idx ON files (file_type);
CREATE INDEX files_furniture_type_idx ON files (furniture_type);
CREATE INDEX files_status_idx ON files (status);
CREATE INDEX files_created_at_idx ON files (created_at);
CREATE INDEX files_product_slug_idx ON files (product_slug);
CREATE INDEX files_link_health_idx ON files (link_health);

-- 8. Create FTS RPC function
CREATE OR REPLACE FUNCTION fts_files(query TEXT)
RETURNS TABLE (
  sha256 TEXT,
  name TEXT,
  file_type TEXT,
  size_bytes BIGINT,
  brand TEXT,
  furniture_type TEXT,
  status TEXT,
  thumbnail_url TEXT,
  source_url TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  description TEXT,
  tags TEXT[],
  product_slug TEXT,
  link_health TEXT,
  search TSVECTOR,
  rank REAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    f.sha256,
    f.name,
    f.file_type,
    f.size_bytes,
    f.brand,
    f.furniture_type,
    f.status,
    f.thumbnail_url,
    f.source_url,
    f.created_at,
    f.updated_at,
    f.description,
    f.tags,
    f.product_slug,
    f.link_health,
    f.search,
    ts_rank(f.search, plainto_tsquery('english', query)) as rank
  FROM files f
  WHERE f.search @@ plainto_tsquery('english', query)
  ORDER BY rank DESC, f.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- 9. Update existing records to populate search vector
UPDATE files SET search = 
  setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
  setweight(to_tsvector('english', COALESCE(brand, '')), 'B') ||
  setweight(to_tsvector('english', COALESCE(furniture_type, '')), 'C') ||
  setweight(to_tsvector('english', COALESCE(array_to_string(tags, ' '), '')), 'D');

-- 10. Create a more sophisticated search function that combines FTS with filters
CREATE OR REPLACE FUNCTION search_files(
  query TEXT,
  file_type_filter TEXT DEFAULT NULL,
  brand_filter TEXT DEFAULT NULL,
  furniture_type_filter TEXT DEFAULT NULL,
  status_filter TEXT DEFAULT NULL,
  min_size BIGINT DEFAULT NULL,
  max_size BIGINT DEFAULT NULL,
  sort_by TEXT DEFAULT 'rank',
  sort_order TEXT DEFAULT 'desc',
  page_num INTEGER DEFAULT 1,
  page_size INTEGER DEFAULT 20
)
RETURNS TABLE (
  sha256 TEXT,
  name TEXT,
  file_type TEXT,
  size_bytes BIGINT,
  brand TEXT,
  furniture_type TEXT,
  status TEXT,
  thumbnail_url TEXT,
  source_url TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  description TEXT,
  tags TEXT[],
  product_slug TEXT,
  link_health TEXT,
  rank REAL,
  total_count BIGINT
) AS $$
DECLARE
  offset_val INTEGER;
  total_count_val BIGINT;
BEGIN
  offset_val := (page_num - 1) * page_size;
  
  -- Get total count
  SELECT COUNT(*) INTO total_count_val
  FROM files f
  WHERE (query IS NULL OR f.search @@ plainto_tsquery('english', query))
    AND (file_type_filter IS NULL OR f.file_type = file_type_filter)
    AND (brand_filter IS NULL OR f.brand = brand_filter)
    AND (furniture_type_filter IS NULL OR f.furniture_type = furniture_type_filter)
    AND (status_filter IS NULL OR f.status = status_filter)
    AND (min_size IS NULL OR f.size_bytes >= min_size)
    AND (max_size IS NULL OR f.size_bytes <= max_size);
  
  RETURN QUERY
  SELECT 
    f.sha256,
    f.name,
    f.file_type,
    f.size_bytes,
    f.brand,
    f.furniture_type,
    f.status,
    f.thumbnail_url,
    f.source_url,
    f.created_at,
    f.updated_at,
    f.description,
    f.tags,
    f.product_slug,
    f.link_health,
    CASE 
      WHEN query IS NULL THEN 0.0
      ELSE ts_rank(f.search, plainto_tsquery('english', query))
    END as rank,
    total_count_val
  FROM files f
  WHERE (query IS NULL OR f.search @@ plainto_tsquery('english', query))
    AND (file_type_filter IS NULL OR f.file_type = file_type_filter)
    AND (brand_filter IS NULL OR f.brand = brand_filter)
    AND (furniture_type_filter IS NULL OR f.furniture_type = furniture_type_filter)
    AND (status_filter IS NULL OR f.status = status_filter)
    AND (min_size IS NULL OR f.size_bytes >= min_size)
    AND (max_size IS NULL OR f.size_bytes <= max_size)
  ORDER BY 
    CASE 
      WHEN sort_by = 'rank' AND sort_order = 'desc' THEN rank
      WHEN sort_by = 'rank' AND sort_order = 'asc' THEN rank
      WHEN sort_by = 'name' AND sort_order = 'desc' THEN 0.0
      WHEN sort_by = 'name' AND sort_order = 'asc' THEN 0.0
      WHEN sort_by = 'created_at' AND sort_order = 'desc' THEN 0.0
      WHEN sort_by = 'created_at' AND sort_order = 'asc' THEN 0.0
      ELSE rank
    END DESC,
    CASE 
      WHEN sort_by = 'name' AND sort_order = 'desc' THEN f.name
      WHEN sort_by = 'name' AND sort_order = 'asc' THEN f.name
      ELSE NULL
    END DESC,
    CASE 
      WHEN sort_by = 'name' AND sort_order = 'asc' THEN f.name
      ELSE NULL
    END ASC,
    CASE 
      WHEN sort_by = 'created_at' AND sort_order = 'desc' THEN f.created_at
      WHEN sort_by = 'created_at' AND sort_order = 'asc' THEN f.created_at
      ELSE NULL
    END DESC,
    CASE 
      WHEN sort_by = 'created_at' AND sort_order = 'asc' THEN f.created_at
      ELSE NULL
    END ASC
  LIMIT page_size OFFSET offset_val;
END;
$$ LANGUAGE plpgsql;

-- 11. Grant necessary permissions (adjust as needed for your setup)
GRANT EXECUTE ON FUNCTION fts_files(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION search_files(TEXT, TEXT, TEXT, TEXT, TEXT, BIGINT, BIGINT, TEXT, TEXT, INTEGER, INTEGER) TO anon;
GRANT USAGE ON SCHEMA public TO anon;
