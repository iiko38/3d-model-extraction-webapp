#!/usr/bin/env python3
import sqlite3

def check_local_paths():
    """Check if local_path values are properly set in the database."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== LOCAL PATHS CHECK ===")
    
    # Check images with local paths
    cursor.execute("SELECT product_uid, image_url, local_path FROM images WHERE local_path IS NOT NULL LIMIT 5")
    images_with_paths = cursor.fetchall()
    
    print("Images with local paths:")
    for product_uid, image_url, local_path in images_with_paths:
        print(f"  {product_uid}")
        print(f"    URL: {image_url[:60]}...")
        print(f"    Local: {local_path}")
        print()
    
    # Check total counts
    cursor.execute("SELECT COUNT(*) FROM images WHERE local_path IS NOT NULL")
    with_paths = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM images")
    total = cursor.fetchone()[0]
    
    print(f"Total images: {total}")
    print(f"Images with local paths: {with_paths}")
    print(f"Images without local paths: {total - with_paths}")
    
    conn.close()

if __name__ == "__main__":
    check_local_paths()
