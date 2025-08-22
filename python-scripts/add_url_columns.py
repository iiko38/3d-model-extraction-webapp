#!/usr/bin/env python3
import sqlite3

def add_url_columns():
    """Add thumbnail_url and product_url columns."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    try:
        # Add thumbnail_url column
        cursor.execute("ALTER TABLE files ADD COLUMN thumbnail_url TEXT")
        print("✅ Added thumbnail_url column")
    except sqlite3.OperationalError as e:
        print(f"⚠️ thumbnail_url: {e}")
    
    try:
        # Add product_url column
        cursor.execute("ALTER TABLE files ADD COLUMN product_url TEXT")
        print("✅ Added product_url column")
    except sqlite3.OperationalError as e:
        print(f"⚠️ product_url: {e}")
    
    conn.commit()
    conn.close()
    print("✅ URL columns added successfully!")

if __name__ == "__main__":
    add_url_columns()
