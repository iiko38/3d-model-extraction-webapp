PRAGMA foreign_keys=OFF;
BEGIN;

-- 2.1 Create the corrected table
CREATE TABLE IF NOT EXISTS files_new (
  product_uid TEXT NOT NULL,
  sha256      TEXT NOT NULL,
  variant     TEXT,
  file_type   TEXT NOT NULL,
  ext         TEXT NOT NULL,
  stored_path TEXT NOT NULL,
  size_bytes  INTEGER,
  source_url  TEXT,
  source_page TEXT,
  PRIMARY KEY (product_uid, sha256)
);

-- 2.2 Copy data, collapsing accidental dupes within the same (product_uid, sha256)
INSERT INTO files_new (product_uid, sha256, variant, file_type, ext, stored_path, size_bytes, source_url, source_page)
SELECT
  product_uid,
  sha256,
  MAX(variant),              -- keep one representative value
  MAX(file_type),
  MAX(ext),
  MAX(stored_path),
  MAX(size_bytes),
  MAX(source_url),
  MAX(source_page)
FROM files
GROUP BY product_uid, sha256;

-- 2.3 Indexes
CREATE INDEX IF NOT EXISTS files_product_idx ON files_new(product_uid);
CREATE INDEX IF NOT EXISTS files_type_idx    ON files_new(file_type);
CREATE INDEX IF NOT EXISTS files_sha_idx     ON files_new(sha256);

-- 2.4 Swap tables
DROP TABLE files;
ALTER TABLE files_new RENAME TO files;

-- 3. Create the images table (variant-aware, idempotent)
CREATE TABLE IF NOT EXISTS images (
  product_uid  TEXT NOT NULL,
  variant      TEXT DEFAULT '' NOT NULL,  -- store '' instead of NULL for PK stability
  image_url    TEXT NOT NULL,
  provider     TEXT NOT NULL,
  score        REAL NOT NULL,
  rationale    TEXT,
  status       TEXT NOT NULL DEFAULT 'pending',  -- 'pending'|'approved'|'rejected'
  width        INTEGER,
  height       INTEGER,
  content_hash TEXT,
  local_path   TEXT,
  created_at   INTEGER NOT NULL,
  updated_at   INTEGER NOT NULL,
  PRIMARY KEY (product_uid, variant, image_url)
);

CREATE INDEX IF NOT EXISTS images_product_idx ON images(product_uid);
CREATE INDEX IF NOT EXISTS images_status_idx  ON images(status);

COMMIT;
PRAGMA foreign_keys=ON;
