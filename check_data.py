#!/usr/bin/env python3
import sqlite3

try:
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    # Check file counts
    cursor.execute("SELECT COUNT(*) FROM files")
    files_count = cursor.fetchone()[0]
    print(f"Total files: {files_count}")
    
    # Check products count
    cursor.execute("SELECT COUNT(*) FROM products")
    products_count = cursor.fetchone()[0]
    print(f"Total products: {products_count}")
    
    # Check URL columns
    cursor.execute("SELECT COUNT(*) FROM files WHERE thumbnail_url IS NOT NULL AND thumbnail_url != ''")
    thumbnail_urls = cursor.fetchone()[0]
    print(f"Files with thumbnail_url: {thumbnail_urls}")
    
    cursor.execute("SELECT COUNT(*) FROM files WHERE product_url IS NOT NULL AND product_url != ''")
    product_urls = cursor.fetchone()[0]
    print(f"Files with product_url: {product_urls}")
    
    # Check furniture types
    cursor.execute("SELECT furniture_type, COUNT(*) FROM files GROUP BY furniture_type ORDER BY COUNT(*) DESC")
    furniture_types = cursor.fetchall()
    print(f"\nFurniture types:")
    for ft, count in furniture_types:
        print(f"  {ft or 'NULL'}: {count}")
    
    # Sample files
    cursor.execute("SELECT sha256, variant, file_type, furniture_type, thumbnail_url FROM files LIMIT 5")
    sample_files = cursor.fetchall()
    print(f"\nSample files:")
    for sha256, variant, file_type, furniture_type, thumbnail_url in sample_files:
        print(f"  {sha256[:8]}... - {variant} ({file_type}) - {furniture_type} - URL: {'Yes' if thumbnail_url else 'No'}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
