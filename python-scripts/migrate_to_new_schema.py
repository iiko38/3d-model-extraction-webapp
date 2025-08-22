#!/usr/bin/env python3
"""
Migration script to refactor 3D warehouse schema
- Remove images table dependency
- Rebuild files table with enhanced schema
- Migrate existing data
- Seed FTS5 index
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Migrate the database to the new schema."""
    db_path = "library/index.sqlite"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("🔄 Starting database migration...")
    
    # Create backup
    backup_path = f"{db_path}.backup"
    if os.path.exists(backup_path):
        os.remove(backup_path)
    os.rename(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    try:
        # Connect to new database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Read and execute schema
        with open('refactor_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Split and execute SQL statements
        statements = schema_sql.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except sqlite3.OperationalError as e:
                    print(f"Warning: Could not execute statement: {e}")
                    print(f"Statement: {statement[:100]}...")
                    continue
        
        print("✅ Schema created successfully")
        
        # Migrate existing data
        migrate_existing_data(cursor)
        
        # Seed FTS5 index
        seed_fts_index(cursor)
        
        conn.commit()
        conn.close()
        
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        # Try to restore backup if possible
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            os.rename(backup_path, db_path)
            print("🔄 Database restored from backup")
        except Exception as restore_error:
            print(f"⚠️ Could not restore backup: {restore_error}")
            print(f"⚠️ Backup is available at: {backup_path}")
        return False

def migrate_existing_data(cursor):
    """Migrate existing data from backup to new schema."""
    print("🔄 Migrating existing data...")
    
    # Connect to backup database
    backup_conn = sqlite3.connect("library/index.sqlite.backup")
    backup_cursor = backup_conn.cursor()
    
    try:
        # Migrate products
        backup_cursor.execute("SELECT * FROM products")
        products = backup_cursor.fetchall()
        
        for product in products:
            cursor.execute("""
                INSERT INTO products (product_uid, brand, name, slug, category, product_card_image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, product)
        
        print(f"✅ Migrated {len(products)} products")
        
        # Migrate files with enhanced schema
        backup_cursor.execute("SELECT * FROM files")
        files = backup_cursor.fetchall()
        
        for file in files:
            # Extract existing columns and add new ones with defaults
            cursor.execute("""
                INSERT INTO files (
                    sha256, product_uid, variant, file_type, ext, stored_path, 
                    size_bytes, source_url, source_page, thumbnail_url, product_url,
                    furniture_type, subtype, tags_csv, url_health, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file[0], file[1], file[2], file[3], file[4], file[5],  # sha256, product_uid, variant, file_type, ext, stored_path
                file[6], file[7], file[8], file[9], file[10],          # size_bytes, source_url, source_page, thumbnail_url, product_url
                None, None, None, 'unknown', 'active'                   # furniture_type, subtype, tags_csv, url_health, status
            ))
        
        print(f"✅ Migrated {len(files)} files")
        
        # Set initial furniture_type based on variant patterns
        set_initial_furniture_types(cursor)
        
        backup_conn.close()
        
    except Exception as e:
        backup_conn.close()
        raise e

def set_initial_furniture_types(cursor):
    """Set initial furniture_type based on variant patterns."""
    print("🔄 Setting initial furniture types...")
    
    # Common furniture type patterns
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

def seed_fts_index(cursor):
    """Seed the FTS5 index with existing data."""
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

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n🎉 Migration completed! You can now run the refactored application.")
    else:
        print("\n💥 Migration failed. Check the error messages above.")
