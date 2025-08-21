#!/usr/bin/env python3
"""
Simple migration script to add new columns to existing tables
"""

import sqlite3
import os

def simple_migration():
    """Add new columns to existing tables without dropping them."""
    db_path = "library/index.sqlite"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("🔄 Starting simple migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if new columns already exist
        cursor.execute("PRAGMA table_info(files)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = [
            ('furniture_type', 'TEXT'),
            ('subtype', 'TEXT'),
            ('tags_csv', 'TEXT'),
            ('url_health', 'TEXT DEFAULT "unknown"'),
            ('status', 'TEXT DEFAULT "active"'),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]
        
        # Add new columns if they don't exist
        for col_name, col_type in new_columns:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE files ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ Could not add {col_name}: {e}")
        
        # Create FTS5 table if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files_fts'")
        if not cursor.fetchone():
            try:
                cursor.execute("""
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
                    )
                """)
                print("✅ Created FTS5 table")
            except sqlite3.OperationalError as e:
                print(f"⚠️ Could not create FTS5 table: {e}")
        
        # Create indexes if they don't exist
        indexes = [
            ('idx_files_product_uid', 'files(product_uid)'),
            ('idx_files_variant', 'files(variant)'),
            ('idx_files_file_type', 'files(file_type)'),
            ('idx_files_furniture_type', 'files(furniture_type)'),
            ('idx_files_status', 'files(status)'),
            ('idx_files_url_health', 'files(url_health)'),
            ('idx_files_thumbnail_url', 'files(thumbnail_url)')
        ]
        
        for index_name, index_def in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
                print(f"✅ Created index: {index_name}")
            except sqlite3.OperationalError as e:
                print(f"⚠️ Could not create index {index_name}: {e}")
        
        # Set initial furniture types based on variant patterns
        print("🔄 Setting initial furniture types...")
        
        patterns = [
            ('chair', 'Chair'),
            ('table', 'Table'),
            ('desk', 'Desk'),
            ('sofa', 'Sofa'),
            ('bed', 'Bed'),
            ('lamp', 'Lamp'),
            ('storage', 'Storage'),
            ('shelf', 'Shelf'),
            ('cabinet', 'Cabinet'),
            ('ottoman', 'Ottoman'),
            ('bench', 'Bench'),
            ('stool', 'Stool'),
            ('dresser', 'Dresser'),
            ('nightstand', 'Nightstand'),
            ('bookcase', 'Bookcase'),
            ('wardrobe', 'Wardrobe'),
            ('mirror', 'Mirror'),
            ('rug', 'Rug'),
            ('curtain', 'Curtain'),
            ('pillow', 'Pillow')
        ]
        
        for pattern, furniture_type in patterns:
            cursor.execute("""
                UPDATE files 
                SET furniture_type = ? 
                WHERE furniture_type IS NULL 
                AND variant LIKE ?
            """, (furniture_type, f'%{pattern}%'))
        
        # Set remaining to 'Other'
        cursor.execute("""
            UPDATE files 
            SET furniture_type = 'Other' 
            WHERE furniture_type IS NULL
        """)
        
        print("✅ Furniture types set")
        
        # Seed FTS5 index if it exists
        try:
            cursor.execute("SELECT COUNT(*) FROM files_fts")
            fts_count = cursor.fetchone()[0]
            if fts_count == 0:
                print("🔄 Seeding FTS5 index...")
                cursor.execute("""
                    INSERT INTO files_fts(rowid, variant, file_type, furniture_type, subtype, tags_csv, brand, name)
                    SELECT 
                        f.rowid,
                        f.variant,
                        f.file_type,
                        f.furniture_type,
                        f.subtype,
                        f.tags_csv,
                        p.brand,
                        p.name
                    FROM files f
                    LEFT JOIN products p ON f.product_uid = p.product_uid
                """)
                print("✅ FTS5 index seeded")
        except sqlite3.OperationalError as e:
            print(f"⚠️ Could not seed FTS5: {e}")
        
        conn.commit()
        conn.close()
        
        print("✅ Simple migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = simple_migration()
    if success:
        print("\n🎉 Migration completed! You can now run the refactored application.")
    else:
        print("\n💥 Migration failed. Check the error messages above.")
