#!/usr/bin/env python3
import sqlite3
from pathlib import Path

def check_downloaded_images():
    """Check the status of downloaded images."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== DOWNLOADED IMAGES CHECK ===")
    
    # Check images with local paths
    cursor.execute("SELECT product_uid, COUNT(*) FROM images WHERE local_path IS NOT NULL GROUP BY product_uid")
    downloaded = cursor.fetchall()
    
    print("Products with downloaded images:")
    for product_uid, count in downloaded:
        print(f"  {product_uid}: {count} images")
    
    # Check total images
    cursor.execute("SELECT COUNT(*) FROM images")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM images WHERE local_path IS NOT NULL")
    downloaded_count = cursor.fetchone()[0]
    
    print(f"\nTotal images: {total}")
    print(f"Downloaded images: {downloaded_count}")
    print(f"Remaining to download: {total - downloaded_count}")
    
    # Check if local files exist
    cursor.execute("SELECT local_path FROM images WHERE local_path IS NOT NULL LIMIT 5")
    local_paths = cursor.fetchall()
    
    print("\nChecking local file existence:")
    for (local_path,) in local_paths:
        path = Path(local_path)
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        print(f"  {local_path}: {'✓' if exists else '✗'} ({size} bytes)")
    
    conn.close()

if __name__ == "__main__":
    check_downloaded_images()
