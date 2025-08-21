import sqlite3
from pathlib import Path

def add_thumbnail_url_column():
    """Add thumbnail_url column to products table."""
    
    # Database path
    db_path = "library/index.sqlite"
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Adding thumbnail_url column to products table...")
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'thumbnail_url' in columns:
            print("  -> thumbnail_url column already exists")
        else:
            # Add the new column
            cursor.execute("ALTER TABLE products ADD COLUMN thumbnail_url TEXT")
            conn.commit()
            print("  -> Successfully added thumbnail_url column")
        
        # Show updated schema
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        print(f"  -> Updated products table columns: {[col[1] for col in columns]}")
        
    except Exception as e:
        print(f"  -> Error adding column: {e}")
        conn.rollback()
    
    conn.close()
    print("✅ Column addition complete!")

if __name__ == "__main__":
    add_thumbnail_url_column()
