#!/usr/bin/env python3
import sqlite3

def create_images_table():
    print("=== CREATING IMAGES TABLE ===")
    
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    # Create the images table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS images (
      product_uid  TEXT NOT NULL,
      variant      TEXT DEFAULT '' NOT NULL,
      image_url    TEXT NOT NULL,
      provider     TEXT NOT NULL,
      score        REAL NOT NULL,
      rationale    TEXT,
      status       TEXT NOT NULL DEFAULT 'pending',
      width        INTEGER,
      height       INTEGER,
      content_hash TEXT,
      local_path   TEXT,
      created_at   INTEGER NOT NULL,
      updated_at   INTEGER NOT NULL,
      PRIMARY KEY (product_uid, variant, image_url)
    );
    """
    
    cursor.execute(create_table_sql)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS images_product_idx ON images(product_uid);")
    cursor.execute("CREATE INDEX IF NOT EXISTS images_status_idx ON images(status);")
    
    conn.commit()
    conn.close()
    
    print("✅ Images table created successfully")
    
    # Verify
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'")
    images_table = cursor.fetchone()
    if images_table:
        print("✅ Images table exists")
        cursor.execute("SELECT COUNT(*) FROM images")
        images_count = cursor.fetchone()[0]
        print(f"Images count: {images_count}")
    else:
        print("❌ Images table not found")
    
    conn.close()

if __name__ == "__main__":
    create_images_table()
