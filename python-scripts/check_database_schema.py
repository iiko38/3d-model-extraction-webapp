import sqlite3
import pandas as pd

def check_database_schema():
    """Check the current database schema and verify columns."""
    
    db_path = "library/index.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Checking Database Schema:")
    print("=" * 60)
    
    # Check products table structure
    print("\n📋 Products Table Columns:")
    cursor.execute("PRAGMA table_info(products)")
    products_columns = cursor.fetchall()
    
    for col in products_columns:
        col_id, col_name, col_type, not_null, default_val, primary_key = col
        print(f"  {col_id:2d}. {col_name:<20} {col_type:<15} {'NOT NULL' if not_null else 'NULL'}")
    
    # Check if thumbnail_url exists
    thumbnail_exists = any(col[1] == 'thumbnail_url' for col in products_columns)
    print(f"\n✅ thumbnail_url column exists: {thumbnail_exists}")
    
    # Check files table structure
    print("\n📋 Files Table Columns:")
    cursor.execute("PRAGMA table_info(files)")
    files_columns = cursor.fetchall()
    
    for col in files_columns:
        col_id, col_name, col_type, not_null, default_val, primary_key = col
        print(f"  {col_id:2d}. {col_name:<20} {col_type:<15} {'NOT NULL' if not_null else 'NULL'}")
    
    # Check images table structure
    print("\n📋 Images Table Columns:")
    cursor.execute("PRAGMA table_info(images)")
    images_columns = cursor.fetchall()
    
    for col in images_columns:
        col_id, col_name, col_type, not_null, default_val, primary_key = col
        print(f"  {col_id:2d}. {col_name:<20} {col_type:<15} {'NOT NULL' if not_null else 'NULL'}")
    
    # Check sample data
    print("\n📊 Sample Data Check:")
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    print(f"  Products: {product_count}")
    
    cursor.execute("SELECT COUNT(*) FROM files")
    file_count = cursor.fetchone()[0]
    print(f"  Files: {file_count}")
    
    cursor.execute("SELECT COUNT(*) FROM images")
    image_count = cursor.fetchone()[0]
    print(f"  Images: {image_count}")
    
    # Check if thumbnail_url has any data
    if thumbnail_exists:
        cursor.execute("SELECT COUNT(*) FROM products WHERE thumbnail_url IS NOT NULL AND thumbnail_url != ''")
        thumbnail_count = cursor.fetchone()[0]
        print(f"  Products with thumbnail_url: {thumbnail_count}")
        
        # Show a few examples
        cursor.execute("SELECT product_uid, name, thumbnail_url FROM products WHERE thumbnail_url IS NOT NULL AND thumbnail_url != '' LIMIT 3")
        examples = cursor.fetchall()
        if examples:
            print("\n📝 Sample thumbnail_url entries:")
            for product_uid, name, thumbnail_url in examples:
                print(f"  {product_uid}: {name}")
                print(f"    URL: {thumbnail_url}")
                print()
    
    conn.close()
    
    return thumbnail_exists

if __name__ == "__main__":
    check_database_schema()
