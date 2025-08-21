#!/usr/bin/env python3
import sqlite3
from pathlib import Path

def fix_image_paths():
    """Fix image paths in the database to be relative to LIB_ROOT."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== FIXING IMAGE PATHS ===")
    
    # Get all images with local paths
    cursor.execute("SELECT product_uid, image_url, local_path FROM images WHERE local_path IS NOT NULL")
    images = cursor.fetchall()
    
    print(f"Found {len(images)} images with local paths")
    
    updated = 0
    for product_uid, image_url, local_path in images:
        # Convert to relative path
        full_path = Path(local_path)
        if full_path.exists():
            # Make it relative to library directory
            relative_path = full_path.relative_to(Path("library"))
            relative_path_str = str(relative_path).replace('\\', '/')  # Use forward slashes for URLs
            
            # Update database
            cursor.execute(
                "UPDATE images SET local_path = ? WHERE product_uid = ? AND image_url = ?",
                (relative_path_str, product_uid, image_url)
            )
            
            print(f"  Updated: {local_path} -> {relative_path_str}")
            updated += 1
        else:
            print(f"  ✗ File not found: {local_path}")
    
    conn.commit()
    conn.close()
    
    print(f"\n=== FIX COMPLETE ===")
    print(f"Updated {updated} image paths")

if __name__ == "__main__":
    fix_image_paths()
