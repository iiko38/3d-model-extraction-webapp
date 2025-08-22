#!/usr/bin/env python3
import sqlite3

try:
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables:", tables)
    
    # Check if files_fts exists
    if 'files_fts' in tables:
        print("✅ FTS5 table exists")
    else:
        print("❌ FTS5 table missing")
    
    # Check files table structure
    if 'files' in tables:
        cursor.execute("PRAGMA table_info(files)")
        columns = [row[1] for row in cursor.fetchall()]
        print("Files table columns:", columns)
        
        # Check for new columns
        new_columns = ['furniture_type', 'subtype', 'tags_csv', 'url_health', 'status']
        for col in new_columns:
            if col in columns:
                print(f"✅ {col} column exists")
            else:
                print(f"❌ {col} column missing")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
