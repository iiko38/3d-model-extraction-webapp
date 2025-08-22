#!/usr/bin/env python3
import sqlite3
import time

def fix_schema():
    print("=== FIXING DATABASE SCHEMA ===")
    
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    # Execute the migration
    print("1. Starting migration...")
    
    # Read the SQL file
    with open('fix_schema.sql', 'r') as f:
        sql_script = f.read()
    
    # Split into individual statements and execute
    statements = sql_script.split(';')
    
    for statement in statements:
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
                print(f"   Executed: {statement[:50]}...")
            except Exception as e:
                print(f"   Error executing: {statement[:50]}... - {e}")
    
    conn.commit()
    conn.close()
    
    print("2. Migration completed!")
    
    # Run sanity checks
    print("\n=== SANITY CHECKS ===")
    
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    # Prove the composite PK exists
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='files'")
    files_schema = cursor.fetchone()
    print(f"Files table schema: {files_schema[0]}")
    
    # Count rows
    cursor.execute("SELECT COUNT(*) FROM files")
    files_count = cursor.fetchone()[0]
    print(f"Files count: {files_count}")
    
    # Ensure no duplicate pairs exist
    cursor.execute("SELECT product_uid, sha256, COUNT(*) c FROM files GROUP BY 1,2 HAVING c>1 LIMIT 5")
    duplicates = cursor.fetchall()
    print(f"Duplicate (product_uid, sha256) pairs: {len(duplicates)}")
    
    # File type breakdown still sane
    cursor.execute("SELECT file_type, COUNT(*) FROM files GROUP BY file_type ORDER BY 2 DESC")
    file_types = cursor.fetchall()
    print("File type breakdown:")
    for ft in file_types:
        print(f"  {ft[0]}: {ft[1]}")
    
    # Check if images table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'")
    images_table = cursor.fetchone()
    if images_table:
        print("✅ Images table created successfully")
        cursor.execute("SELECT COUNT(*) FROM images")
        images_count = cursor.fetchone()[0]
        print(f"Images count: {images_count}")
    else:
        print("❌ Images table not found")
    
    conn.close()
    
    print("\n=== SCHEMA FIX COMPLETED ===")

if __name__ == "__main__":
    fix_schema()
