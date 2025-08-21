-- 3D Warehouse Refactor Schema
-- Remove images dependency, enhance files table, add FTS5, triggers

-- Drop existing tables and recreate
DROP TABLE IF EXISTS images;
DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS products;

-- Create products table
CREATE TABLE products (
    product_uid TEXT PRIMARY KEY,
    brand TEXT NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    category TEXT,
    product_card_image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create enhanced files table
CREATE TABLE files (
    sha256 TEXT PRIMARY KEY,
    product_uid TEXT NOT NULL,
    variant TEXT NOT NULL,
    file_type TEXT NOT NULL,
    ext TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    source_url TEXT,
    source_page TEXT,
    thumbnail_url TEXT,
    product_url TEXT,
    furniture_type TEXT,
    subtype TEXT,
    tags_csv TEXT,
    url_health TEXT DEFAULT 'unknown', -- unknown, healthy, broken, checking
    status TEXT DEFAULT 'active', -- active, archived, processing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_uid) REFERENCES products(product_uid)
);

-- Create FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE files_fts USING fts5(
    sha256 UNINDEXED,
    product_uid UNINDEXED,
    variant,
    file_type,
    furniture_type,
    subtype,
    tags_csv,
    brand UNINDEXED,
    name UNINDEXED,
    content='files',
    content_rowid='rowid'
);

-- Create triggers for FTS5 synchronization
CREATE TRIGGER files_ai AFTER INSERT ON files BEGIN
    INSERT INTO files_fts(rowid, variant, file_type, furniture_type, subtype, tags_csv, brand, name)
    VALUES (new.rowid, new.variant, new.file_type, new.furniture_type, new.subtype, new.tags_csv,
            (SELECT brand FROM products WHERE product_uid = new.product_uid),
            (SELECT name FROM products WHERE product_uid = new.product_uid));
END;

CREATE TRIGGER files_ad AFTER DELETE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, variant, file_type, furniture_type, subtype, tags_csv, brand, name)
    VALUES('delete', old.rowid, old.variant, old.file_type, old.furniture_type, old.subtype, old.tags_csv,
           (SELECT brand FROM products WHERE product_uid = old.product_uid),
           (SELECT name FROM products WHERE product_uid = old.product_uid));
END;

CREATE TRIGGER files_au AFTER UPDATE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, variant, file_type, furniture_type, subtype, tags_csv, brand, name)
    VALUES('delete', old.rowid, old.variant, old.file_type, old.furniture_type, old.subtype, old.tags_csv,
           (SELECT brand FROM products WHERE product_uid = old.product_uid),
           (SELECT name FROM products WHERE product_uid = old.product_uid));
    INSERT INTO files_fts(rowid, variant, file_type, furniture_type, subtype, tags_csv, brand, name)
    VALUES (new.rowid, new.variant, new.file_type, new.furniture_type, new.subtype, new.tags_csv,
            (SELECT brand FROM products WHERE product_uid = new.product_uid),
            (SELECT name FROM products WHERE product_uid = new.product_uid));
END;

-- Create indexes for performance
CREATE INDEX idx_files_product_uid ON files(product_uid);
CREATE INDEX idx_files_variant ON files(variant);
CREATE INDEX idx_files_file_type ON files(file_type);
CREATE INDEX idx_files_furniture_type ON files(furniture_type);
CREATE INDEX idx_files_status ON files(status);
CREATE INDEX idx_files_url_health ON files(url_health);
CREATE INDEX idx_files_thumbnail_url ON files(thumbnail_url);

-- Create view for easy querying with product info
CREATE VIEW files_with_products AS
SELECT 
    f.*,
    p.brand,
    p.name as product_name,
    p.slug as product_slug,
    p.category
FROM files f
LEFT JOIN products p ON f.product_uid = p.product_uid;

-- Create trigger to update updated_at timestamp
CREATE TRIGGER files_update_timestamp 
    AFTER UPDATE ON files
    FOR EACH ROW
BEGIN
    UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE sha256 = NEW.sha256;
END;

CREATE TRIGGER products_update_timestamp 
    AFTER UPDATE ON products
    FOR EACH ROW
BEGIN
    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE product_uid = NEW.product_uid;
END;
